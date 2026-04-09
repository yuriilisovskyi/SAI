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
     create  -- attribute defaults from JSON as kwargs, with two special rules:
                  * attributes carrying a "condition" field are skipped
                  * "empty" / "empty list" defaults are replaced with the
                    appropriate Thrift empty list/object constructed from the
                    attribute's "type" field (e.g. sai_thrift_object_list_t(count=0, idlist=[]))
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
  ""              → skipped  (no default)
  "empty"         → Thrift empty list object constructed from "type"
  "empty list"    → Thrift empty list object constructed from "type"
  "internal"      → skipped
  "attrvalue …"   → skipped
  "true/false"    → True / False
  "0" / SAI_NULL_OBJECT_ID → 0
  integer string  → int literal
  anything else   → passed as a string constant (SAI enum name, IP, …)

  Attributes with "condition" are excluded from create calls entirely.

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
import sai_thrift.sai_headers as _sai_headers
import sai_thrift.ttypes as _ttypes

# Default JSON: repo_root/sai_api_attributes.json
_DEFAULT_JSON = os.path.join(_REPO_DIR, 'sai_api_attributes.json')


# ---------------------------------------------------------------------------
# Empty SAI object / list construction
# ---------------------------------------------------------------------------

def _build_empty_list_type_map() -> dict:
    """
    Scan sai_thrift.ttypes at import time and build a mapping:
        sai_<X>_list_t  →  sai_thrift_<X>_list_t  (the Thrift class)

    Every such class has the constructor signature
        __init__(self, count, <listfield>)
    where <listfield> is the name of the list argument (idlist, int32list, …).
    We record (cls, listfield_name) so we can call cls(count=0, listfield=[]).
    """
    mapping: dict[str, tuple] = {}
    for attr_name in dir(_ttypes):
        cls = getattr(_ttypes, attr_name)
        if not (isinstance(cls, type) and attr_name.endswith('_list_t')):
            continue
        try:
            sig = inspect.signature(cls.__init__)
            params = [p for p in sig.parameters if p != 'self']
            # Expected: ['count', '<listfield>']
            if len(params) == 2 and params[0] == 'count':
                sai_name = attr_name.replace('sai_thrift_', 'sai_', 1)
                mapping[sai_name] = (cls, params[1])
        except (ValueError, TypeError):
            pass
    return mapping


# sai_<X>_list_t → (ThriftClass, list_field_name)
_EMPTY_LIST_MAP: dict[str, tuple] = _build_empty_list_type_map()

# attribute_value_t field names that are scalar (True/integer is safe to pass)
_SCALAR_ATTR_VALUE_FIELDS = frozenset({
    'booldata', 's32', 'u32', 'u64', 'u8', 'u16', 's8', 's16', 's64', 'ptr',
    'oid', 'objid', 'mac', 'ip4', 'ip6', 'ipaddr', 'ipprefix', 'chardata',
    'u128', 'u16data', 'encrypt_key', 'auth_key', 'authkey',
    'macsecsak', 'macsecauthkey', 'macsecsalt',
    'latchstatus', 'sysportconfig', 'timespec', 'json', 'reachability',
    'portpowerconsumption', 'rx_state', 'u32range', 's32range', 'u16range',
    'prbs_ber', 'aclfield', 'aclaction', 'aclmask',
})

# attribute_value_t field name → Thrift empty-object factory for non-scalar types.
# For *list fields we use _EMPTY_LIST_MAP via sai_type.  The entries here cover
# the non-list complex types that appear in get_*_attribute functions.
def _build_attr_value_field_to_empty():
    t = _ttypes
    def _list_factory(cls_name, list_field):
        cls = getattr(t, cls_name, None)
        if cls is None:
            return None
        return lambda: cls(count=0, **{list_field: []})

    mapping = {}
    # List types
    for field, cls_name, lf in [
        ('objlist',              'sai_thrift_object_list_t',              'idlist'),
        ('s32list',              'sai_thrift_s32_list_t',                 'int32list'),
        ('u32list',              'sai_thrift_u32_list_t',                 'uint32list'),
        ('u8list',               'sai_thrift_u8_list_t',                  'uint8list'),
        ('s8list',               'sai_thrift_s8_list_t',                  'int8list'),
        ('u16list',              'sai_thrift_u16_list_t',                 'uint16list'),
        ('s16list',              'sai_thrift_s16_list_t',                 'int16list'),
        ('u64list',              'sai_thrift_u64_list_t',                 'uint64list') if hasattr(t, 'sai_thrift_u64_list_t') else ('u64list', None, None),
        ('maplist',              'sai_thrift_map_list_t',                 'maplist'),
        ('vlanlist',             'sai_thrift_vlan_list_t',                'idlist'),
        ('ipaddrlist',           'sai_thrift_ip_address_list_t',          'addresslist'),
        ('segmentlist',          'sai_thrift_segment_list_t',             'ip6list'),
        ('tlvlist',              'sai_thrift_tlv_list_t',                 'tlvlist'),
        ('sysportconfiglist',    'sai_thrift_system_port_config_list_t',  'configlist'),
        ('aclresource',          'sai_thrift_acl_resource_list_t',        'resourcelist'),
        ('aclchainlist',         'sai_thrift_acl_chain_list_t',           'chainlist'),
        ('u16rangelist',         'sai_thrift_u16_range_list_t',           'rangelist'),
        ('ipprefixlist',         'sai_thrift_ip_prefix_list_t',           'prefixlist') if hasattr(t, 'sai_thrift_ip_prefix_list_t') else ('ipprefixlist', None, None),
        ('portlanelatchstatuslist', 'sai_thrift_port_lane_latch_status_list_t', 'statuslist'),
        ('portfrequencyoffsetppmlist', 'sai_thrift_port_frequency_offset_ppm_list_t', 'valueslist'),
        ('portsnrlist',          'sai_thrift_port_snr_list_t',            'valueslist'),
        ('porteyevalues',        'sai_thrift_port_eye_values_list_t',     'valueslist'),
        ('portpam4eyevalues',    'sai_thrift_port_pam4_eye_values_list_t','valueslist'),
        ('prbs_rx_status_list',  'sai_thrift_prbs_per_lane_rx_status_list_t', 'statuslist'),
        ('prbs_rx_state_list',   'sai_thrift_prbs_per_lane_rx_state_list_t',  'statelist'),
        ('prbs_ber_list',        'sai_thrift_prbs_per_lane_bit_error_rate_list_t', 'ratelist'),
        ('porterror',            'sai_thrift_port_err_status_list_t',     'statuslist'),
        ('portserdestaps',       'sai_thrift_taps_list_t',                'listlist') if hasattr(t, 'sai_thrift_taps_list_t') else ('portserdestaps', None, None),
    ]:
        if cls_name is None:
            continue
        factory = _list_factory(cls_name, lf)
        if factory:
            mapping[field] = factory

    # Non-list complex types: construct with all-None/defaults
    acl_cap_cls = getattr(t, 'sai_thrift_acl_capability_t', None)
    if acl_cap_cls:
        mapping['aclcapability'] = lambda: acl_cap_cls(
            is_action_list_mandatory=False,
            action_list=_ttypes.sai_thrift_s32_list_t(count=0, int32list=[]),
        )
    return mapping


_ATTR_VALUE_FIELD_TO_EMPTY = _build_attr_value_field_to_empty()

# Cache: fn_callable → {param_name: attr_value_field}
_GET_PARAM_VTYPE_CACHE: dict = {}

# Sentinel used as the vtype for scalar get params
_SCALAR = '__scalar__'

def _get_param_value_types(fn_callable) -> dict:
    """
    Parse the adapter function source and return a mapping:
        {param_name: vtype}

    where vtype is either:
      _SCALAR            — param uses a bare attribute_t (pass True)
      '<field_name>'     — param uses attribute_value_t(field=...) (pass empty obj)

    Two adapter patterns exist:
      Scalar:    if X is not None:\n    attribute = sai_thrift_attribute_t(...)
      Non-scalar: if X is not None:\n    attribute_value = sai_thrift_attribute_value_t(field=X)
    """
    fn_id = id(fn_callable)
    if fn_id in _GET_PARAM_VTYPE_CACHE:
        return _GET_PARAM_VTYPE_CACHE[fn_id]
    try:
        src = inspect.getsource(fn_callable)
    except (OSError, TypeError):
        return {}

    result = {}
    # Non-scalar: attribute_value_t used
    for param, vtype in re.findall(
        r'if (\w+) is not None:\s*\n\s*attribute_value = sai_thrift_attribute_value_t\((\w+)\s*=',
        src,
    ):
        result[param] = vtype

    # Scalar: no attribute_value, just attribute_t directly
    for param in re.findall(
        r'if (\w+) is not None:\s*\n\s*attribute = sai_thrift_attribute_t\(',
        src,
    ):
        if param not in result:   # non-scalar takes priority if both matched
            result[param] = _SCALAR

    _GET_PARAM_VTYPE_CACHE[fn_id] = result
    return result


def _make_get_value_for_param(param: str, vtype: str):
    """
    Return the appropriate value to pass for a get_*_attribute parameter:
      - True  for scalar params (tells adapter to retrieve the attribute)
      - an empty Thrift list/struct object for non-scalar types
      - None  if no factory is known (param will be skipped)
    """
    if vtype is _SCALAR or vtype in _SCALAR_ATTR_VALUE_FIELDS:
        return True
    factory = _ATTR_VALUE_FIELD_TO_EMPTY.get(vtype)
    if factory:
        return factory()
    # Unknown complex type — skip
    return None


def _make_empty_thrift_object(sai_type: str):
    """
    Construct an appropriate empty Thrift object for a SAI attribute type
    whose default value is "empty" or "empty list".

    The SAI type string may be compound (e.g. "sai_s32_list_t sai_port_fec_mode_t");
    only the first token is used for lookup.

    Returns None if no matching Thrift constructor is found (the caller will
    then skip the attribute).
    """
    base_type = sai_type.split()[0].strip()   # first token only

    entry = _EMPTY_LIST_MAP.get(base_type)
    if entry:
        cls, list_field = entry
        return cls(count=0, **{list_field: []})

    return None


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

def _render_default(raw: str, sai_type: str = ''):
    """
    Convert a raw default string from the JSON into a Python value suitable
    as a keyword argument.  Returns None when no usable default is available.

    "empty" / "empty list" → Thrift empty list/object built from sai_type;
                              None if no Thrift constructor is known for the type.
    SAI_* constant strings  → resolved to their enum/integer value via
                              sai_thrift.sai_headers; returned as-is if not found
                              (the adapter will handle the name lookup itself for
                              string-accepting fields).
    """
    if not raw or raw in ('internal',) or raw.startswith('attrvalue'):
        return None
    low = raw.lower()
    if low in ('empty', 'empty list'):
        return _make_empty_thrift_object(sai_type)
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
    # SAI enum constant name: resolve to the actual enum/integer via sai_headers
    if raw.startswith('SAI_'):
        resolved = getattr(_sai_headers, raw, None)
        if resolved is not None:
            return resolved
    # IP address, MAC, vendor string, or unknown SAI name — pass through as string
    return raw


def _attr_default(attr_val) -> object:
    """
    Extract and render the default value from a JSON attribute entry.
    attr_val is a dict with keys "type", "def_value", and optionally "condition".
    """
    if isinstance(attr_val, dict):
        return _render_default(attr_val.get('def_value', ''),
                               attr_val.get('type', ''))
    # Legacy plain-string fallback (should not occur with current JSON)
    return _render_default(str(attr_val))


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

    def _create_kwargs(self, attributes: dict, fn_callable=None) -> dict:
        """
        Build kwargs dict for a create call from the attributes JSON.

        Rules:
          - Attributes with a "condition" field are skipped; their validity
            depends on other attribute values that may not hold here.
          - "empty" / "empty list" defaults are replaced with the appropriate
            Thrift empty list/object constructed from the "type" field.
          - If fn_callable is provided, kwargs are filtered to only the
            parameters the function actually accepts (avoids passing read-only
            attributes like port_list that are not in the create signature).
        """
        accepted = None
        if fn_callable is not None:
            accepted = set(_fn_params(fn_callable))

        kwargs = {}
        for attr_name, attr_val in attributes.items():
            # Skip conditional attributes in create calls
            if isinstance(attr_val, dict) and 'condition' in attr_val:
                continue
            param = _attr_to_param(attr_name)
            # Skip params the target function does not accept
            if accepted is not None and param not in accepted:
                continue
            value = _attr_default(attr_val)
            if value is not None:
                kwargs[param] = value
        return kwargs

    def _get_kwargs(self, attributes: dict, fn_callable=None) -> dict:
        """
        Build kwargs dict for a get call.

        For scalar attribute value types (bool, s32, u32, …) pass True to tell
        the adapter to retrieve that attribute.
        For list/struct types (objlist, s32list, maplist, …) the adapter
        serialises the argument as-is, so we must pass an empty Thrift object
        instead of True to avoid 'bool has no attribute write' errors.

        fn_callable, if provided, is used to look up the per-param value type.
        Without it every param falls back to True (safe for scalar-only objects).
        """
        if fn_callable is None:
            return {_attr_to_param(attr_name): True for attr_name in attributes}

        param_vtypes = _get_param_value_types(fn_callable)
        kwargs = {}
        for attr_name in attributes:
            param = _attr_to_param(attr_name)
            vtype = param_vtypes.get(param)
            if vtype is None:
                # Param not found in adapter source (read-only or unknown): skip
                continue
            value = _make_get_value_for_param(param, vtype)
            if value is not None:
                kwargs[param] = value
        return kwargs

    def _set_kwargs_list(self, attributes: dict) -> list[tuple[str, object]]:
        """Return a list of (param, value) pairs for individual set calls."""
        pairs = []
        for attr_name, attr_val in attributes.items():
            value = _attr_default(attr_val)
            if value is not None:
                pairs.append((_attr_to_param(attr_name), value))
        return pairs

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_value(v) -> str:
        """Format a single argument value for the pre-call log line."""
        if isinstance(v, bool):
            return str(v)
        # Thrift struct with __repr__ that shows type name
        cls_name = type(v).__name__
        if cls_name.startswith('sai_thrift_'):
            # Show class name + count for list types, full repr otherwise
            if hasattr(v, 'count'):
                return f'{cls_name}(count={v.count})'
            return repr(v)
        # Enum-like objects (SAI constants after resolution)
        if hasattr(v, 'name') and hasattr(v, 'value'):
            return f'{v.name}({v.value})'
        return repr(v)

    def _log_call(self, fn_name: str, pos_args: list, kwargs: dict) -> None:
        """
        Print a structured pre-call log block, e.g.::

          Calling sai_thrift_create_bridge(
            type                          = SAI_BRIDGE_TYPE_1Q(0)
            max_learned_addresses         = 0
            learn_disable                 = False
            selective_counter_list        = sai_thrift_object_list_t(count=0)
          )
        """
        parts = []
        for v in pos_args:
            parts.append(f'    {self._fmt_value(v)}')
        for k, v in kwargs.items():
            parts.append(f'    {k:<36s} = {self._fmt_value(v)}')
        if parts:
            print(f'  Calling {fn_name}(')
            for p in parts:
                print(p)
            print('  )')
        else:
            print(f'  Calling {fn_name}()')

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

        kwargs = self._create_kwargs(attributes, fn_callable=fn)
        self._log_call(fn_name, [], kwargs)
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

        kwargs = self._get_kwargs(attributes, fn_callable=fn)
        # Belt-and-suspenders: only keep params the function accepts
        accepted = set(params)
        kwargs = {k: v for k, v in kwargs.items() if k in accepted}

        self._log_call(fn_name, pos_args, kwargs)
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
            self._log_call(fn_name, pos_args, {param: value})
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
        """
        Execute a stats_get or stats_clear call.

        Positional args after client:
          1. OID (or entry) — required for non-global objects
          2. mode           — required by stats_ext functions; supplied as
                             SAI_STATS_MODE_READ when present with no default
        """
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

        # Detect required positional params with no default (e.g. 'mode' in stats_ext)
        try:
            sig = inspect.signature(fn)
        except (ValueError, TypeError):
            sig = None
        if sig:
            for pname, p in sig.parameters.items():
                if pname in ('client', key_param):
                    continue
                if (p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                               inspect.Parameter.POSITIONAL_OR_KEYWORD)
                        and p.default is inspect.Parameter.empty):
                    # Required positional — supply SAI_STATS_MODE_READ
                    mode_val = getattr(_sai_headers, 'SAI_STATS_MODE_READ', 1)
                    pos_args.append(mode_val)
                    break  # only one such param expected

        self._log_call(fn_name, pos_args, {})
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

        self._log_call(fn_name, pos_args, {})
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
