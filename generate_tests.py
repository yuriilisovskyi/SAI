#!/usr/bin/env python3
"""
Generate PTF test cases from sai_api_attributes.json.

For every SAI object type the generator produces a single PTF test class that:
  - inherits from ThriftInterface (ptf/sai_base_test.py)
  - in runTest() calls every Thrift function listed in "functions"
  - for CRUD functions (create / get / set / remove) uses all attributes
    from "attributes" as keyword arguments
  - for stats, bulk, and other helpers, calls the function with minimal /
    sensible placeholder arguments

Output: ptf/sai_generated_tests.py
"""

import json
import os
import re
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "sai_api_attributes.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "ptf", "sai_generated_tests.py")

# ---------------------------------------------------------------------------
# Attribute name -> Python parameter name
# e.g. SAI_ACL_COUNTER_ATTR_TABLE_ID -> table_id
# ---------------------------------------------------------------------------

def attr_to_param(attr_name: str) -> str:
    """Convert SAI attribute constant to the Thrift function keyword arg name.

    The adapter prefixes parameter names that start with a digit with '_'
    (e.g. SAI_PORT_ATTR_1000X_SGMII_SLAVE_AUTODETECT -> _1000x_sgmii_slave_autodetect).
    """
    marker = "_ATTR_"
    idx = attr_name.find(marker)
    if idx == -1:
        return attr_name.lower()
    param = attr_name[idx + len(marker):].lower()
    if param and param[0].isdigit():
        param = "_" + param
    return param


# ---------------------------------------------------------------------------
# Default-value rendering
# ---------------------------------------------------------------------------

# Types whose default can be rendered as a Python literal
_BOOL_VALS = {"true": "True", "false": "False"}

# Object-id sentinels
_OID_SENTINELS = {"SAI_NULL_OBJECT_ID", "0"}

def _render_default(attr_name: str, raw_default: str) -> str:
    """
    Convert a raw default value string from the CSV/JSON into a Python
    literal that can be used as a keyword argument value in a Thrift call.

    Rules (in priority order):
      - empty / internal / attrvalue  -> None
      - bool literal                  -> True / False
      - SAI_NULL_OBJECT_ID / 0 (oid) -> 0
      - plain integer string          -> integer literal
      - hex string (0x...)            -> hex integer literal
      - everything else               -> quoted string constant
    """
    if not raw_default or raw_default in ("internal", "") or raw_default.startswith("attrvalue"):
        return "None"
    if raw_default == "empty":
        return "None"
    lower = raw_default.lower()
    if lower in _BOOL_VALS:
        return _BOOL_VALS[lower]
    if raw_default in _OID_SENTINELS:
        return "0"
    if re.fullmatch(r"-?\d+", raw_default):
        return raw_default
    if re.fullmatch(r"0[xX][0-9a-fA-F]+", raw_default):
        return raw_default
    # SAI constant or IP address / MAC / other string
    return repr(raw_default)


def _render_attr_value(attr_name: str, attr_val) -> str:
    """
    Render a single attribute entry from the JSON as a (param_name, value_repr) pair.

    attr_val is either a plain string default or a dict with
    {validonly|condition: [...], def_value: "..."}.
    """
    param = attr_to_param(attr_name)
    if isinstance(attr_val, dict):
        raw = attr_val.get("def_value", "")
    else:
        raw = attr_val
    return param, _render_default(attr_name, raw)


# ---------------------------------------------------------------------------
# Function-call classification
# ---------------------------------------------------------------------------

def _classify(fn: str):
    """
    Return one of: 'create', 'remove', 'get', 'set',
                   'stats_get', 'stats_clear',
                   'bulk_create', 'bulk_remove', 'bulk_get', 'bulk_set',
                   'other'
    """
    if fn.startswith("sai_thrift_create_"):
        return "create"
    if fn.startswith("sai_thrift_remove_"):
        return "remove"
    if fn.startswith("sai_thrift_set_") and fn.endswith("_attribute"):
        return "set"
    if fn.startswith("sai_thrift_get_") and fn.endswith("_attribute"):
        return "get"
    if fn.startswith("sai_thrift_get_") and "_stats" in fn:
        return "stats_get"
    if fn.startswith("sai_thrift_clear_"):
        return "stats_clear"
    if fn.startswith("sai_thrift_bulk_create_"):
        return "bulk_create"
    if fn.startswith("sai_thrift_bulk_remove_"):
        return "bulk_remove"
    if fn.startswith("sai_thrift_bulk_get_"):
        return "bulk_get"
    if fn.startswith("sai_thrift_bulk_set_"):
        return "bulk_set"
    return "other"


def _object_name_from_fn(fn: str, cls: str) -> str:
    """
    Extract the object name fragment from a function name.
    e.g. 'sai_thrift_create_acl_table' -> 'acl_table'
         'sai_thrift_get_acl_table_attribute' -> 'acl_table'
         'sai_thrift_get_vlan_stats' -> 'vlan'
         'sai_thrift_clear_vlan_stats' -> 'vlan'
    """
    prefixes = {
        "create":      "sai_thrift_create_",
        "remove":      "sai_thrift_remove_",
        "set":         "sai_thrift_set_",
        "get":         "sai_thrift_get_",
        "stats_get":   "sai_thrift_get_",
        "stats_clear": "sai_thrift_clear_",
        "bulk_create": "sai_thrift_bulk_create_",
        "bulk_remove": "sai_thrift_bulk_remove_",
        "bulk_get":    "sai_thrift_bulk_get_",
        "bulk_set":    "sai_thrift_bulk_set_",
        "other":       "sai_thrift_",
    }
    suffix_strip = {
        "set": "_attribute",
        "get": "_attribute",
        "stats_get": "_stats_ext",
        "bulk_get": "_attribute",
        "bulk_set": "_attribute",
    }
    name = fn
    pre = prefixes.get(cls, "sai_thrift_")
    if name.startswith(pre):
        name = name[len(pre):]
    suf = suffix_strip.get(cls, "")
    if suf and name.endswith(suf):
        name = name[: -len(suf)]
    # also strip plain _stats suffix
    if name.endswith("_stats"):
        name = name[: -len("_stats")]
    return name


# Objects whose create/remove/get/set do NOT take an OID (global singletons)
_GLOBAL_OBJECTS = {"switch", "switch_tunnel"}

# Objects that use an entry struct instead of a plain OID
_ENTRY_OBJECTS: set[str] = set()  # populated from adapter scan


def _load_entry_objects(adapter_path: str) -> set[str]:
    """
    Scan sai_adapter.py and collect object names whose remove/get/set
    takes an *_entry positional parameter (not *_oid).
    """
    entry_objs: set[str] = set()
    if not os.path.isfile(adapter_path):
        return entry_objs
    with open(adapter_path, errors="replace") as f:
        content = f.read()
    # e.g.  def sai_thrift_remove_fdb_entry(client, fdb_entry):
    for m in re.finditer(
        r"^def (sai_thrift_(?:remove|get|set)_(\w+?)(?:_attribute)?)\(client,\s+(\w+_entry)",
        content,
        re.MULTILINE,
    ):
        obj_name = m.group(2)
        entry_objs.add(obj_name)
    return entry_objs


# ---------------------------------------------------------------------------
# Code generation helpers
# ---------------------------------------------------------------------------

def _obj_type_to_class_name(obj_type: str) -> str:
    """SAI_OBJECT_TYPE_ACL_TABLE -> SaiAclTableTest"""
    suffix = obj_type.replace("SAI_OBJECT_TYPE_", "")
    return "Sai" + "".join(w.capitalize() for w in suffix.split("_")) + "Test"


def _obj_type_to_var(obj_type: str) -> str:
    """SAI_OBJECT_TYPE_ACL_TABLE -> acl_table"""
    return obj_type.replace("SAI_OBJECT_TYPE_", "").lower()


def _attr_kwargs_lines(attributes: dict, indent: int = 20) -> list[str]:
    """
    Build a list of 'param=value' strings for all attributes.
    Lines are intended for use inside a function call.
    """
    parts = []
    for attr_name, attr_val in attributes.items():
        param, val = _render_attr_value(attr_name, attr_val)
        if val == "None":
            continue  # skip attributes without a usable default
        parts.append(f"{param}={val}")
    return parts


def _build_get_kwargs(attributes: dict) -> list[str]:
    """
    For get_*_attribute calls pass each attr as attr_name=True.
    We skip attributes whose names conflict with the oid param.
    """
    parts = []
    for attr_name in attributes:
        param = attr_to_param(attr_name)
        parts.append(f"{param}=True")
    return parts


def _build_set_kwargs(attributes: dict) -> list[str]:
    """
    For set_*_attribute: pick attributes that have a usable default and
    are not read-only (heuristic: skip if name contains LIST, COUNT, NUMBER
    unless they have a non-empty default).
    """
    parts = []
    for attr_name, attr_val in attributes.items():
        param, val = _render_attr_value(attr_name, attr_val)
        if val == "None":
            continue
        parts.append(f"{param}={val}")
    return parts


# ---------------------------------------------------------------------------
# Per-function call code generation
# ---------------------------------------------------------------------------

def _gen_create_call(fn: str, obj_name: str, var: str, attrs: dict,
                     entry_objs: set[str]) -> list[str]:
    lines = []
    kwargs = _attr_kwargs_lines(attrs)
    is_entry = obj_name in entry_objs
    is_global = obj_name in _GLOBAL_OBJECTS

    if is_entry:
        entry_var = f"self.{var}_entry"
        call_args = [f"self.client", entry_var]
    elif is_global:
        call_args = ["self.client"]
    else:
        call_args = ["self.client"]

    # Build the call
    all_args = call_args + kwargs
    call_str = _format_call(f"self.{var}_oid = {fn}", all_args)
    lines += call_str
    if not is_entry and not is_global:
        lines.append(
            f"        self.assertNotEqual(self.{var}_oid, SAI_NULL_OBJECT_ID)"
        )
    return lines


def _gen_get_call(fn: str, obj_name: str, var: str, attrs: dict,
                  entry_objs: set[str]) -> list[str]:
    lines = []
    kwargs = _build_get_kwargs(attrs)
    if not kwargs:
        lines.append(f"        # {fn}: no gettable attributes")
        return lines

    is_entry = obj_name in entry_objs
    is_global = obj_name in _GLOBAL_OBJECTS

    if is_entry:
        oid_arg = f"self.{var}_entry"
    elif is_global:
        oid_arg = None
    else:
        oid_arg = f"self.{var}_oid"

    call_args = (["self.client"] + ([oid_arg] if oid_arg else []) + kwargs)
    call_str = _format_call(f"attr = {fn}", call_args)
    lines += call_str
    lines.append(f"        self.assertIsNotNone(attr)")
    return lines


def _gen_set_call(fn: str, obj_name: str, var: str, attrs: dict,
                  entry_objs: set[str]) -> list[str]:
    lines = []
    kwargs = _build_set_kwargs(attrs)
    if not kwargs:
        lines.append(f"        # {fn}: no settable attributes with defaults")
        return lines

    is_entry = obj_name in entry_objs
    is_global = obj_name in _GLOBAL_OBJECTS

    if is_entry:
        oid_arg = f"self.{var}_entry"
    elif is_global:
        oid_arg = None
    else:
        oid_arg = f"self.{var}_oid"

    # set only one attribute at a time (SAI convention); use the first
    first_kwarg = kwargs[0]
    call_args = (["self.client"] + ([oid_arg] if oid_arg else []) + [first_kwarg])
    call_str = _format_call(f"status = {fn}", call_args)
    lines += call_str
    lines.append(
        f"        self.assertEqual(status, SAI_STATUS_SUCCESS)"
    )
    return lines


def _gen_remove_call(fn: str, obj_name: str, var: str,
                     entry_objs: set[str]) -> list[str]:
    is_entry = obj_name in entry_objs
    is_global = obj_name in _GLOBAL_OBJECTS

    if is_entry:
        oid_arg = f"self.{var}_entry"
    elif is_global:
        oid_arg = None
    else:
        oid_arg = f"self.{var}_oid"

    call_args = ["self.client"] + ([oid_arg] if oid_arg else [])
    return _format_call(f"status = {fn}", call_args) + [
        f"        self.assertEqual(status, SAI_STATUS_SUCCESS)"
    ]


def _gen_stats_get_call(fn: str, obj_name: str, var: str,
                        entry_objs: set[str]) -> list[str]:
    is_entry = obj_name in entry_objs
    is_global = obj_name in _GLOBAL_OBJECTS
    if is_entry:
        oid_arg = f"self.{var}_entry"
    elif is_global:
        oid_arg = None
    else:
        oid_arg = f"self.{var}_oid"
    call_args = ["self.client"] + ([oid_arg] if oid_arg else [])
    return _format_call(f"stats = {fn}", call_args)


def _gen_stats_clear_call(fn: str, obj_name: str, var: str,
                          entry_objs: set[str]) -> list[str]:
    is_entry = obj_name in entry_objs
    is_global = obj_name in _GLOBAL_OBJECTS
    if is_entry:
        oid_arg = f"self.{var}_entry"
    elif is_global:
        oid_arg = None
    else:
        oid_arg = f"self.{var}_oid"
    call_args = ["self.client"] + ([oid_arg] if oid_arg else [])
    return _format_call(f"status = {fn}", call_args) + [
        f"        self.assertEqual(status, SAI_STATUS_SUCCESS)"
    ]


def _gen_bulk_call(fn: str, obj_name: str, var: str,
                   entry_objs: set[str]) -> list[str]:
    """Bulk calls are emitted as a commented stub — they need custom entry lists."""
    return [
        f"        # TODO: bulk call requires a list of entries/attrs: {fn}",
        f"        # {fn}(self.client, ...)",
    ]


def _gen_other_call(fn: str) -> list[str]:
    return [
        f"        # {fn}(self.client, ...)  # custom arguments required",
    ]


def _format_call(lhs: str, args: list[str], base_indent: int = 8) -> list[str]:
    """
    Format a Python function call, wrapping long lines cleanly.
    Returns a list of source lines (each ending without \\n).
    """
    indent = " " * base_indent
    cont_indent = " " * (base_indent + 4)
    full = f"{indent}{lhs}({', '.join(args)})"
    if len(full) <= 100:
        return [full]
    # Multi-line
    lines = [f"{indent}{lhs}("]
    for i, arg in enumerate(args):
        sep = "," if i < len(args) - 1 else ""
        lines.append(f"{cont_indent}{arg}{sep}")
    lines.append(f"{indent})")
    return lines


# ---------------------------------------------------------------------------
# Full test class generation
# ---------------------------------------------------------------------------

def gen_test_class(obj_type: str, obj_data: dict, entry_objs: set[str]) -> str:
    """Generate a complete PTF test class for one SAI object type."""
    functions = obj_data.get("functions", [])
    attributes = obj_data.get("attributes", {})
    var = _obj_type_to_var(obj_type)
    class_name = _obj_type_to_class_name(obj_type)
    obj_name = var  # same as var but kept separate for clarity

    body_lines: list[str] = []

    # Detect whether this object uses entry structs
    is_entry = obj_name in entry_objs
    is_global = obj_name in _GLOBAL_OBJECTS

    # ---- setUp ----
    body_lines.append("    def setUp(self):")
    body_lines.append("        super().setUp()")
    if is_entry:
        body_lines.append(
            f"        self.{var}_entry = None  "
            f"# TODO: construct sai_thrift_{var}_t entry"
        )
    elif not is_global:
        body_lines.append(f"        self.{var}_oid = SAI_NULL_OBJECT_ID")
    body_lines.append("")

    # ---- runTest ----
    if not functions:
        body_lines.append("    def runTest(self):")
        body_lines.append(f"        pass  # No Thrift functions defined for {obj_type}")
        body_lines.append("")
        body_lines.append("    def tearDown(self):")
        body_lines.append("        super().tearDown()")
        return _assemble_class(class_name, obj_type, body_lines)

    # Group functions by classification for ordered emission:
    # create -> get -> set -> stats_get -> stats_clear -> bulk -> other -> remove
    classified: dict[str, list[str]] = {}
    for fn in functions:
        cls = _classify(fn)
        classified.setdefault(cls, []).append(fn)

    runtest_lines: list[str] = []

    def emit(lines):
        runtest_lines.extend(lines)
        runtest_lines.append("")

    # --- create ---
    for fn in classified.get("create", []):
        fn_obj = _object_name_from_fn(fn, "create")
        emit(
            [f"        # {fn}"]
            + _gen_create_call(fn, fn_obj, var, attributes, entry_objs)
        )

    # --- get ---
    for fn in classified.get("get", []):
        fn_obj = _object_name_from_fn(fn, "get")
        emit(
            [f"        # {fn}"]
            + _gen_get_call(fn, fn_obj, var, attributes, entry_objs)
        )

    # --- set ---
    for fn in classified.get("set", []):
        fn_obj = _object_name_from_fn(fn, "set")
        emit(
            [f"        # {fn}"]
            + _gen_set_call(fn, fn_obj, var, attributes, entry_objs)
        )

    # --- stats_get ---
    for fn in classified.get("stats_get", []):
        fn_obj = _object_name_from_fn(fn, "stats_get")
        emit(
            [f"        # {fn}"]
            + _gen_stats_get_call(fn, fn_obj, var, entry_objs)
        )

    # --- stats_clear ---
    for fn in classified.get("stats_clear", []):
        fn_obj = _object_name_from_fn(fn, "stats_clear")
        emit(
            [f"        # {fn}"]
            + _gen_stats_clear_call(fn, fn_obj, var, entry_objs)
        )

    # --- bulk ---
    for fn in (classified.get("bulk_create", []) + classified.get("bulk_remove", [])
               + classified.get("bulk_get", []) + classified.get("bulk_set", [])):
        emit([f"        # {fn}"] + _gen_bulk_call(fn, obj_name, var, entry_objs))

    # --- other ---
    for fn in classified.get("other", []):
        emit([f"        # {fn}"] + _gen_other_call(fn))

    # --- remove (last, in reverse create order) ---
    for fn in reversed(classified.get("remove", [])):
        fn_obj = _object_name_from_fn(fn, "remove")
        emit(
            [f"        # {fn}"]
            + _gen_remove_call(fn, fn_obj, var, entry_objs)
        )

    # Ensure runTest body has at least one real statement (comments-only => SyntaxError)
    has_real_stmt = any(
        ln.strip() and not ln.strip().startswith("#")
        for ln in runtest_lines
    )

    body_lines.append("    def runTest(self):")
    body_lines.extend(runtest_lines)
    if not has_real_stmt:
        body_lines.append("        pass  # All functions require custom arguments")
    body_lines.append("")

    # ---- tearDown ----
    body_lines.append("    def tearDown(self):")
    # Clean up OID if create was present
    if classified.get("remove") and not is_entry and not is_global:
        remove_fn = classified["remove"][0]
        oid_arg = f"self.{var}_oid"
        body_lines.append(f"        if self.{var}_oid != SAI_NULL_OBJECT_ID:")
        call_lines = _format_call(remove_fn, ["self.client", oid_arg], base_indent=12)
        body_lines.extend(call_lines)
    elif classified.get("remove") and is_entry:
        remove_fn = classified["remove"][0]
        body_lines.append(f"        if self.{var}_entry is not None:")
        body_lines.append(
            f"            {remove_fn}(self.client, self.{var}_entry)"
        )
    body_lines.append("        super().tearDown()")

    return _assemble_class(class_name, obj_type, body_lines)


def _assemble_class(class_name: str, obj_type: str, body_lines: list[str]) -> str:
    header = [
        f"class {class_name}(ThriftInterface):",
        f'    """Auto-generated test for {obj_type}."""',
        "",
    ]
    return "\n".join(header + body_lines) + "\n"


# ---------------------------------------------------------------------------
# File-level generation
# ---------------------------------------------------------------------------

FILE_HEADER = '''\
# Auto-generated by generate_tests.py — DO NOT EDIT MANUALLY
# Re-generate by running: python3 generate_tests.py
"""
PTF test cases for all SAI object types.

Each class exercises every Thrift function defined for the object type,
using the attribute default values from sai_api_attributes.json as
call arguments.

Usage:
    ptf --test-dir ptf sai_generated_tests.<TestClassName> \\
        --interface 0@eth0 ...
"""

import sys
import os

# Make sai_thrift importable when running from the ptf directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sai_base_test import ThriftInterface
from sai_thrift.sai_headers import *
from sai_thrift.sai_adapter import *
import sai_thrift.sai_adapter as adapter

SAI_NULL_OBJECT_ID = 0

'''


def generate(json_path: str, output_path: str, adapter_path: str) -> None:
    with open(json_path) as f:
        data: dict = json.load(f)

    global _ENTRY_OBJECTS
    _ENTRY_OBJECTS = _load_entry_objects(adapter_path)

    parts = [FILE_HEADER]
    for obj_type in sorted(data.keys()):
        obj_data = data[obj_type]
        parts.append(f"# {'=' * 74}")
        parts.append(f"# {obj_type}")
        parts.append(f"# {'=' * 74}")
        parts.append("")
        parts.append(gen_test_class(obj_type, obj_data, _ENTRY_OBJECTS))
        parts.append("")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(parts))

    print(f"Written {len(data)} test classes to {output_path}")


if __name__ == "__main__":
    adapter_path = os.path.join(
        SCRIPT_DIR,
        "test", "saithriftv2", "build", "lib", "sai_thrift", "sai_adapter.py",
    )
    generate(JSON_PATH, OUTPUT_PATH, adapter_path)
