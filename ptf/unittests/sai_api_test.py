"""
SAI API dynamic test suite.

This module provides:

  SaiApiTestBase  -- base class with the full execution engine.  Sub-classes
                     (or the built-in SaiApiTest) point it at a JSON file and
                     an optional object-type filter; the engine does the rest.

  SaiApiTest      -- ready-to-run PTF test that loads sai_api_attributes.json
                     and exercises every object type that has at least one
                     Thrift function mapped.

Engine overview
---------------
For each SAI object type in the JSON the engine:

1. Resolves the callable for every function listed under "functions" by
   looking it up in the sai_thrift.sai_adapter module.

2. Introspects the function signature to determine the key argument
   (OID or entry struct) and the full set of attribute keyword args.

3. Classifies functions as create / get / set / remove / stats / bulk / other.

4. Executes the full CRUD lifecycle:
     create  -- attribute kwargs derived from "attributes" defaults in JSON
     get     -- every attribute passed as <param>=True
     set     -- each settable attribute individually (SAI allows one at a time)
     stats   -- OID / entry only (counter_ids use adapter defaults)
     remove  -- OID or entry

Attribute-name ↔ kwarg-name mapping
------------------------------------
  SAI_VLAN_ATTR_MAX_LEARNED_ADDRESSES → max_learned_addresses
  SAI_PORT_ATTR_1000X_SGMII_SLAVE_AUTODETECT → _1000x_sgmii_slave_autodetect

Default-value rendering
-----------------------
  ""             → skipped  (no default)
  "empty"        → skipped
  "internal"     → skipped
  "attrvalue …"  → skipped
  "true/false"   → True / False
  "0" / SAI_NULL_OBJECT_ID → 0
  integer string → int literal
  anything else  → passed as a string constant (SAI enum name, IP, …)

Layout note
-----------
This file lives in ptf/unittests/.  The repository root is two levels up
(__file__ → ptf/unittests/sai_api_test.py → ../../).
ptf/ is added to sys.path so that sai_base_test and sai_thrift imports work
identically to the other PTF tests in ptf/.
"""

import inspect
import json
import os
import re
import sys

# ptf/ directory must be on sys.path so that sai_base_test, sai_thrift, etc.
# can be imported the same way as every other PTF test.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))   # ptf/unittests/
_PTF_DIR  = os.path.dirname(_THIS_DIR)                   # ptf/
_REPO_DIR = os.path.dirname(_PTF_DIR)                    # repo root

if _PTF_DIR not in sys.path:
    sys.path.insert(0, _PTF_DIR)

from sai_base_test import ThriftInterface
from sai_thrift.sai_headers import *
import sai_thrift.sai_adapter as _adapter

# Default JSON: repo_root/sai_api_attributes.json
_DEFAULT_JSON = os.path.join(_REPO_DIR, 'sai_api_attributes.json')


# ---------------------------------------------------------------------------
# Attribute / parameter name conversion
# ---------------------------------------------------------------------------

def _attr_to_param(attr_name: str) -> str:
    """
    Convert a SAI attribute constant to the sai_adapter keyword-arg name.

    SAI_VLAN_ATTR_MAX_LEARNED_ADDRESSES  →  max_learned_addresses
    SAI_PORT_ATTR_1000X_SGMII_SLAVE_AUTODETECT  →  _1000x_sgmii_slave_autodetect
    """
    idx = attr_name.find('_ATTR_')
    if idx == -1:
        return attr_name.lower()
    param = attr_name[idx + len('_ATTR_'):].lower()
    if param and param[0].isdigit():
        param = '_' + param
    return param


# ---------------------------------------------------------------------------
# Default value rendering
# ---------------------------------------------------------------------------

def _render_default(raw: str):
    """
    Convert a raw default string from the JSON into a Python value suitable
    as a keyword argument.  Returns None when no usable default is available.
    """
    if not raw or raw in ('internal', 'empty') or raw.startswith('attrvalue'):
        return None
    low = raw.lower()
    if low == 'true':
        return True
    if low == 'false':
        return False
    if raw in ('SAI_NULL_OBJECT_ID', '0'):
        return 0
    if re.fullmatch(r'-?\d+', raw):
        return int(raw)
    if re.fullmatch(r'0[xX][0-9a-fA-F]+', raw):
        return int(raw, 16)
    # SAI enum constant, IP address, MAC, vendor string, etc.
    return raw


def _attr_default(attr_val) -> object:
    """
    Extract and render the default value from a JSON attribute entry.
    attr_val is either a plain string or a dict with a "def_value" key.
    """
    if isinstance(attr_val, dict):
        return _render_default(attr_val.get('def_value', ''))
    return _render_default(attr_val)


# ---------------------------------------------------------------------------
# Function classification
# ---------------------------------------------------------------------------

def _classify(fn_name: str) -> str:
    """
    Return one of:
      'create', 'remove', 'get', 'set',
      'stats_get', 'stats_clear',
      'bulk', 'other'
    """
    if fn_name.startswith('sai_thrift_create_'):
        return 'create'
    if fn_name.startswith('sai_thrift_remove_'):
        return 'remove'
    if fn_name.startswith('sai_thrift_set_') and fn_name.endswith('_attribute'):
        return 'set'
    if fn_name.startswith('sai_thrift_get_') and fn_name.endswith('_attribute'):
        return 'get'
    if ('_stats' in fn_name) and fn_name.startswith('sai_thrift_get_'):
        return 'stats_get'
    if fn_name.startswith('sai_thrift_clear_'):
        return 'stats_clear'
    if fn_name.startswith('sai_thrift_bulk_'):
        return 'bulk'
    return 'other'


# ---------------------------------------------------------------------------
# Function introspection
# ---------------------------------------------------------------------------

def _fn_params(fn_callable) -> list:
    """Return the list of parameter names (excluding 'client')."""
    try:
        sig = inspect.signature(fn_callable)
    except (ValueError, TypeError):
        return []
    return [
        name for name, p in sig.parameters.items()
        if name != 'client'
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL,
                           inspect.Parameter.VAR_KEYWORD)
    ]


def _key_param(params: list) -> str | None:
    """
    Return the positional 'key' parameter name (OID or entry struct),
    or None for global singletons (e.g. switch remove/get/set).

    Key params are the *first* parameter when it ends with '_oid' or '_entry'.
    For create functions there is no incoming OID.
    """
    if not params:
        return None
    first = params[0]
    if first.endswith('_oid') or first.endswith('_entry'):
        return first
    return None


# ---------------------------------------------------------------------------
# Base test class
# ---------------------------------------------------------------------------

class SaiApiTestBase(ThriftInterface):
    """
    Dynamic SAI API test base.

    Sub-class and set class attributes to customise:

        json_path    -- absolute path or path relative to the repo root for
                        sai_api_attributes.json (or a per-header JSON in sai_data/).
                        Defaults to repo_root/sai_api_attributes.json.
        object_types -- iterable of SAI_OBJECT_TYPE_* strings to test;
                        None means test all types in the JSON.
        stop_on_fail -- if True (default False), stop the whole suite on the
                        first function-call failure; otherwise record and continue.

    Example sub-class that only tests VLAN and Bridge::

        class MyVlanBridgeTest(SaiApiTestBase):
            object_types = ['SAI_OBJECT_TYPE_VLAN', 'SAI_OBJECT_TYPE_BRIDGE']
    """

    json_path: str = _DEFAULT_JSON
    object_types: list | None = None
    stop_on_fail: bool = False

    # ------------------------------------------------------------------
    # PTF lifecycle
    # ------------------------------------------------------------------

    def setUp(self):
        super().setUp()
        self._load_json()
        self._results = {}   # obj_type -> {fn_name: 'PASS'|'SKIP'|'FAIL: <msg>'}

    def runTest(self):
        types_to_test = self.object_types or sorted(self._data.keys())
        for obj_type in types_to_test:
            if obj_type not in self._data:
                print(f'[WARN] {obj_type} not found in JSON – skipping')
                continue
            self._test_object_type(obj_type, self._data[obj_type])
        self._report()

    def tearDown(self):
        super().tearDown()

    # ------------------------------------------------------------------
    # Core engine
    # ------------------------------------------------------------------

    def _load_json(self):
        path = (
            self.json_path
            if os.path.isabs(self.json_path)
            else os.path.normpath(os.path.join(_REPO_DIR, self.json_path))
        )
        with open(path) as f:
            self._data = json.load(f)

    def _test_object_type(self, obj_type: str, obj_data: dict):
        """Run the full lifecycle for one SAI object type."""
        functions = obj_data.get('functions', [])
        attributes = obj_data.get('attributes', {})

        if not functions:
            print(f'[{obj_type}] No Thrift functions – skipped')
            return

        print(f'\n=== {obj_type} ===')
        self._results[obj_type] = {}

        # Group by category
        classified = {}
        for fn in functions:
            cat = _classify(fn)
            classified.setdefault(cat, []).append(fn)

        # State carried across the lifecycle for this object type
        ctx = {'oid': None}   # oid == None until create succeeds

        # Execute in lifecycle order
        for fn in classified.get('create', []):
            self._exec_create(fn, attributes, ctx, obj_type)
            if self.stop_on_fail and self._results[obj_type].get(fn, '').startswith('FAIL'):
                return

        for fn in classified.get('get', []):
            self._exec_get(fn, attributes, ctx, obj_type)

        for fn in classified.get('set', []):
            self._exec_set(fn, attributes, ctx, obj_type)

        for fn in classified.get('stats_get', []):
            self._exec_keyed(fn, ctx, obj_type)

        for fn in classified.get('stats_clear', []):
            self._exec_keyed(fn, ctx, obj_type)

        for fn in classified.get('bulk', []):
            self._record(obj_type, fn, 'SKIP: bulk operations require custom entry lists')

        for fn in classified.get('other', []):
            self._record(obj_type, fn, 'SKIP: requires custom arguments')

        for fn in reversed(classified.get('remove', [])):
            self._exec_remove(fn, ctx, obj_type)

    # ------------------------------------------------------------------
    # Per-category execution helpers
    # ------------------------------------------------------------------

    def _resolve(self, fn_name: str):
        """Return the callable from sai_adapter, or None if not present."""
        return getattr(_adapter, fn_name, None)

    def _create_kwargs(self, attributes: dict) -> dict:
        """Build kwargs dict for a create call from the attributes JSON."""
        kwargs = {}
        for attr_name, attr_val in attributes.items():
            param = _attr_to_param(attr_name)
            value = _attr_default(attr_val)
            if value is not None:
                kwargs[param] = value
        return kwargs

    def _get_kwargs(self, attributes: dict) -> dict:
        """Build kwargs dict for a get call: every attr as param=True."""
        return {_attr_to_param(attr_name): True for attr_name in attributes}

    def _set_kwargs_list(self, attributes: dict) -> list[tuple[str, object]]:
        """Return a list of (param, value) pairs for individual set calls."""
        pairs = []
        for attr_name, attr_val in attributes.items():
            value = _attr_default(attr_val)
            if value is not None:
                pairs.append((_attr_to_param(attr_name), value))
        return pairs

    def _call(self, fn_callable, *args, **kwargs):
        """Invoke the Thrift function and return (result, error_string_or_None)."""
        try:
            result = fn_callable(self.client, *args, **kwargs)
            return result, None
        except Exception as exc:
            return None, str(exc)

    # ------------------------------------------------------------------

    def _exec_create(self, fn_name: str, attributes: dict, ctx: dict,
                     obj_type: str):
        fn = self._resolve(fn_name)
        if fn is None:
            self._record(obj_type, fn_name, 'SKIP: not in sai_adapter')
            return

        params = _fn_params(fn)
        key_param = _key_param(params)
        if key_param and key_param.endswith('_entry'):
            self._record(obj_type, fn_name,
                         'SKIP: entry-type create requires a pre-built entry struct')
            return

        kwargs = self._create_kwargs(attributes)
        result, err = self._call(fn, **kwargs)
        if err:
            self._record(obj_type, fn_name, f'FAIL: {err}')
        else:
            ctx['oid'] = result
            self._record(obj_type, fn_name, 'PASS')
            print(f'  [PASS] {fn_name} → oid={result}')

    def _exec_get(self, fn_name: str, attributes: dict, ctx: dict,
                  obj_type: str):
        fn = self._resolve(fn_name)
        if fn is None:
            self._record(obj_type, fn_name, 'SKIP: not in sai_adapter')
            return

        params = _fn_params(fn)
        key_param = _key_param(params)

        pos_args = []
        if key_param:
            if key_param.endswith('_entry'):
                self._record(obj_type, fn_name,
                             'SKIP: entry-type get requires a pre-built entry struct')
                return
            if ctx['oid'] is None:
                self._record(obj_type, fn_name,
                             'SKIP: no OID available (create skipped/failed)')
                return
            pos_args = [ctx['oid']]

        kwargs = self._get_kwargs(attributes)
        accepted = set(params)
        kwargs = {k: v for k, v in kwargs.items() if k in accepted}

        result, err = self._call(fn, *pos_args, **kwargs)
        if err:
            self._record(obj_type, fn_name, f'FAIL: {err}')
        else:
            self._record(obj_type, fn_name, 'PASS')
            print(f'  [PASS] {fn_name}')

    def _exec_set(self, fn_name: str, attributes: dict, ctx: dict,
                  obj_type: str):
        fn = self._resolve(fn_name)
        if fn is None:
            self._record(obj_type, fn_name, 'SKIP: not in sai_adapter')
            return

        params = _fn_params(fn)
        key_param = _key_param(params)

        pos_args = []
        if key_param:
            if key_param.endswith('_entry'):
                self._record(obj_type, fn_name,
                             'SKIP: entry-type set requires a pre-built entry struct')
                return
            if ctx['oid'] is None:
                self._record(obj_type, fn_name,
                             'SKIP: no OID available (create skipped/failed)')
                return
            pos_args = [ctx['oid']]

        pairs = self._set_kwargs_list(attributes)
        accepted = set(params)
        pairs = [(k, v) for k, v in pairs if k in accepted]

        if not pairs:
            self._record(obj_type, fn_name, 'SKIP: no settable attributes with defaults')
            return

        # SAI set_*_attribute accepts only one attribute at a time
        all_pass = True
        for param, value in pairs:
            result, err = self._call(fn, *pos_args, **{param: value})
            if err:
                self._record(obj_type, fn_name, f'FAIL: {param}={value!r}: {err}')
                all_pass = False
                if self.stop_on_fail:
                    return
        if all_pass:
            self._record(obj_type, fn_name, 'PASS')
            print(f'  [PASS] {fn_name} ({len(pairs)} attribute(s) set)')

    def _exec_keyed(self, fn_name: str, ctx: dict, obj_type: str):
        """Execute a stats_get or stats_clear — only needs the OID."""
        fn = self._resolve(fn_name)
        if fn is None:
            self._record(obj_type, fn_name, 'SKIP: not in sai_adapter')
            return

        params = _fn_params(fn)
        key_param = _key_param(params)

        pos_args = []
        if key_param:
            if key_param.endswith('_entry'):
                self._record(obj_type, fn_name,
                             'SKIP: entry-type stats require a pre-built entry struct')
                return
            if ctx['oid'] is None:
                self._record(obj_type, fn_name,
                             'SKIP: no OID available (create skipped/failed)')
                return
            pos_args = [ctx['oid']]

        result, err = self._call(fn, *pos_args)
        if err:
            self._record(obj_type, fn_name, f'FAIL: {err}')
        else:
            self._record(obj_type, fn_name, 'PASS')
            print(f'  [PASS] {fn_name}')

    def _exec_remove(self, fn_name: str, ctx: dict, obj_type: str):
        fn = self._resolve(fn_name)
        if fn is None:
            self._record(obj_type, fn_name, 'SKIP: not in sai_adapter')
            return

        params = _fn_params(fn)
        key_param = _key_param(params)

        pos_args = []
        if key_param:
            if key_param.endswith('_entry'):
                self._record(obj_type, fn_name,
                             'SKIP: entry-type remove requires a pre-built entry struct')
                return
            if ctx['oid'] is None:
                self._record(obj_type, fn_name,
                             'SKIP: no OID available (create skipped/failed)')
                return
            pos_args = [ctx['oid']]

        result, err = self._call(fn, *pos_args)
        if err:
            self._record(obj_type, fn_name, f'FAIL: {err}')
        else:
            ctx['oid'] = None   # consumed
            self._record(obj_type, fn_name, 'PASS')
            print(f'  [PASS] {fn_name}')

    # ------------------------------------------------------------------
    # Result tracking
    # ------------------------------------------------------------------

    def _record(self, obj_type: str, fn_name: str, status: str):
        self._results.setdefault(obj_type, {})[fn_name] = status
        if status.startswith('FAIL'):
            print(f'  [FAIL] {fn_name}: {status[6:]}')
        elif status.startswith('SKIP'):
            print(f'  [SKIP] {fn_name}: {status[6:]}')

    def _report(self):
        """Print a summary and fail the test if any FAIL was recorded."""
        totals = {'PASS': 0, 'SKIP': 0, 'FAIL': 0}
        failures = []
        for obj_type, fns in self._results.items():
            for fn, status in fns.items():
                key = status.split(':')[0]
                totals[key] = totals.get(key, 0) + 1
                if key == 'FAIL':
                    failures.append(f'{obj_type}.{fn}: {status}')

        print('\n' + '=' * 70)
        print(f'Results: PASS={totals["PASS"]}  SKIP={totals["SKIP"]}  FAIL={totals["FAIL"]}')
        if failures:
            print('Failures:')
            for f in failures:
                print(f'  {f}')
        print('=' * 70)

        if failures:
            self.fail(f'{len(failures)} function(s) failed – see output above')


# ---------------------------------------------------------------------------
# Concrete ready-to-run test class
# ---------------------------------------------------------------------------

class SaiApiTest(SaiApiTestBase):
    """
    Exercises every SAI object type present in sai_api_attributes.json.

    Run with PTF::

        ptf --test-dir ptf/unittests sai_api_test.SaiApiTest \\
            --interface 0@<iface> \\
            --test-params "thrift_server='localhost'"

    To restrict to specific object types, sub-class and set ``object_types``::

        class SaiVlanTest(SaiApiTestBase):
            object_types = ['SAI_OBJECT_TYPE_VLAN']
    """
    pass
