#!/usr/bin/env python3
"""
Combine sai_api_list.csv and sai_attr_defaults.csv into a single JSON file
that maps each SAI object type to its Thrift functions and attribute defaults.

For attributes that have @validonly or @condition annotations in the SAI header,
the attribute value uses an extended structure:

  Plain attribute (no annotation):
    "<attr_name>": "<default_value>"

  Attribute with @validonly:
    "<attr_name>": {"validonly": [<clauses>], "def_value": "<default_value>"}

  Attribute with @condition:
    "<attr_name>": {"condition": [<clauses>], "def_value": "<default_value>"}

Each clause is a dict mapping a guard attribute name to either:
  - a single value string  (ATTR_A == X)
  - a list of value strings (ATTR_A == X or ATTR_A == Y, same guard attr)
  - the boolean string "true" / "false"

AND is represented as multiple clause dicts in the list (all must hold).
Mixed AND+OR with parentheses is decomposed accordingly.

Example:
  @validonly SAI_TUNNEL_ATTR_PEER_MODE == SAI_TUNNEL_PEER_MODE_P2P
  -> "validonly": [{"SAI_TUNNEL_ATTR_PEER_MODE": "SAI_TUNNEL_PEER_MODE_P2P"}]

  @condition SAI_X == A or SAI_X == B
  -> "condition": [{"SAI_X": ["A", "B"]}]

  @validonly SAI_A == X and SAI_B == Y
  -> "validonly": [{"SAI_A": "X"}, {"SAI_B": "Y"}]

  @validonly SAI_A == X and (SAI_B == Y or SAI_B == Z)
  -> "validonly": [{"SAI_A": "X"}, {"SAI_B": ["Y", "Z"]}]
"""

import csv
import glob
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INC_DIR = os.path.join(SCRIPT_DIR, 'inc')
API_CSV = os.path.join(SCRIPT_DIR, 'sai_api_list.csv')
ATTR_CSV = os.path.join(SCRIPT_DIR, 'sai_attr_defaults.csv')
OUTPUT_JSON = os.path.join(SCRIPT_DIR, 'sai_api_attributes.json')


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def load_functions(api_csv):
    """Return dict: SAI object type -> sorted list of unique Thrift functions."""
    obj_functions: dict[str, list[str]] = {}
    with open(api_csv, newline='') as f:
        for row in csv.DictReader(f):
            obj_type = row['SAI object'].strip()
            thrift_fn = row['Python Thrift function'].strip()
            if not thrift_fn or obj_type == 'SAI_OBJECT_TYPE_NULL':
                continue
            obj_functions.setdefault(obj_type, [])
            if thrift_fn not in obj_functions[obj_type]:
                obj_functions[obj_type].append(thrift_fn)
    for obj_type in obj_functions:
        obj_functions[obj_type].sort()
    return obj_functions


def attr_to_object_type(attr_name: str) -> str:
    """Derive SAI_OBJECT_TYPE_<X> from SAI_<X>_ATTR_<FIELD>."""
    idx = attr_name.find('_ATTR_')
    if idx == -1 or not attr_name.startswith('SAI_'):
        return '(unknown)'
    return 'SAI_OBJECT_TYPE_' + attr_name[4:idx]


def load_attributes(attr_csv):
    """Return dict: SAI object type -> {attr_name: default_value_string}."""
    obj_attrs: dict[str, dict[str, str]] = {}
    with open(attr_csv, newline='') as f:
        for row in csv.DictReader(f):
            attr_name = row['attribute_name'].strip()
            default = row['default_value'].strip()
            obj_type = attr_to_object_type(attr_name)
            obj_attrs.setdefault(obj_type, {})
            obj_attrs[obj_type][attr_name] = default
    return obj_attrs


# ---------------------------------------------------------------------------
# Header annotation parser
# ---------------------------------------------------------------------------

def _parse_or_group(expr: str) -> dict:
    """
    Parse a single OR-group: one guard attribute equated to one or more values.

    e.g. "SAI_X == A or SAI_X == B"  ->  {"SAI_X": ["A", "B"]}
         "SAI_X == A"                 ->  {"SAI_X": "A"}
         "SAI_X == true"              ->  {"SAI_X": "true"}
    """
    parts = [p.strip() for p in re.split(r'\bor\b', expr)]
    # Validate: each part must be "ATTR == VALUE"
    guard_attr = None
    values = []
    for p in parts:
        m = re.match(r'(SAI_\w+)\s*==\s*(\S+)', p)
        if not m:
            return {"_raw": expr.strip()}
        attr, val = m.group(1), m.group(2)
        if guard_attr is None:
            guard_attr = attr
        elif guard_attr != attr:
            # OR over different attributes — keep raw
            return {"_raw": expr.strip()}
        values.append(val)
    if guard_attr is None:
        return {"_raw": expr.strip()}
    return {guard_attr: values[0] if len(values) == 1 else values}


def _parse_annotation_expr(expr: str) -> list:
    """
    Parse a @validonly / @condition expression into a list of clause dicts.

    Supported patterns (in increasing complexity):
      A == X
      A == X or A == Y             (same attr, OR)
      A == X or B == Y             (different attrs, OR — kept as _raw)
      A == X and B == Y            (AND of two simple clauses)
      A == X and (B == Y or B == Z) (AND of simple + OR-group)

    Returns: list of clause dicts; each dict has exactly one key.
    """
    expr = expr.strip()

    # Split on top-level 'and' (not inside parentheses)
    and_parts = _split_top_level_and(expr)

    clauses = []
    for part in and_parts:
        part = part.strip().strip('(').strip(')')
        clause = _parse_or_group(part)
        clauses.append(clause)
    return clauses


def _split_top_level_and(expr: str) -> list:
    """
    Split on ' and ' that is not inside parentheses.
    Returns list of sub-expressions.
    """
    parts = []
    depth = 0
    current = []
    tokens = re.split(r'(\(|\)|\band\b)', expr)
    for tok in tokens:
        if tok == '(':
            depth += 1
            current.append(tok)
        elif tok == ')':
            depth -= 1
            current.append(tok)
        elif tok == 'and' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(tok)
    if current:
        parts.append(''.join(current).strip())
    return [p for p in parts if p]


def parse_header_annotations(inc_dir: str) -> dict[str, dict]:
    """
    Scan all inc/*.h files and return a dict:
      attr_name -> {"validonly": [...]}  or  {"condition": [...]}

    Only attributes that have exactly one of @validonly or @condition are
    included (no attribute has both, as confirmed by inspection).
    """
    annotations: dict[str, dict] = {}

    # Pattern: a Doxygen block /** ... */ immediately followed by SAI_*_ATTR_*
    block_re = re.compile(
        r'/\*\*(.*?)\*/\s*(SAI_[A-Z0-9_]+_ATTR_[A-Z0-9_]+)',
        re.DOTALL,
    )

    for filepath in sorted(glob.glob(os.path.join(inc_dir, '*.h'))):
        with open(filepath, errors='replace') as f:
            content = f.read()

        for m in block_re.finditer(content):
            block, attr_name = m.group(1), m.group(2)

            # Extract @validonly / @condition lines (could span the rest of the tag line)
            validonly_m = re.search(r'@validonly\s+(.+)', block)
            condition_m = re.search(r'@condition\s+(.+)', block)

            if validonly_m:
                expr = validonly_m.group(1).strip()
                annotations[attr_name] = {
                    'validonly': _parse_annotation_expr(expr),
                }
            elif condition_m:
                expr = condition_m.group(1).strip()
                annotations[attr_name] = {
                    'condition': _parse_annotation_expr(expr),
                }

    return annotations


# ---------------------------------------------------------------------------
# Combine
# ---------------------------------------------------------------------------

def build_combined(obj_functions, obj_attrs, annotations):
    """
    Merge functions, attributes (with annotation metadata), keyed by object type.
    """
    all_obj_types = sorted(set(obj_functions) | set(obj_attrs))
    combined = {}
    for obj_type in all_obj_types:
        if obj_type == '(unknown)':
            continue

        attrs_raw = obj_attrs.get(obj_type, {})
        attrs_out = {}
        for attr_name, default_val in attrs_raw.items():
            ann = annotations.get(attr_name)
            if ann:
                ann_key = 'validonly' if 'validonly' in ann else 'condition'
                attrs_out[attr_name] = {
                    ann_key: ann[ann_key],
                    'def_value': default_val,
                }
            else:
                attrs_out[attr_name] = default_val

        combined[obj_type] = {
            'functions': obj_functions.get(obj_type, []),
            'attributes': attrs_out,
        }
    return combined


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    obj_functions = load_functions(API_CSV)
    obj_attrs = load_attributes(ATTR_CSV)
    annotations = parse_header_annotations(INC_DIR)

    combined = build_combined(obj_functions, obj_attrs, annotations)

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(combined, f, indent=2)

    annotated = sum(
        1
        for obj_data in combined.values()
        for v in obj_data['attributes'].values()
        if isinstance(v, dict)
    )
    fn_total = sum(len(v['functions']) for v in combined.values())
    attr_total = sum(len(v['attributes']) for v in combined.values())

    print(f"Written {len(combined)} object types to {OUTPUT_JSON}")
    print(f"  {fn_total} Thrift functions")
    print(f"  {attr_total} attributes total")
    print(f"  {annotated} attributes with @validonly / @condition metadata")

    unknown_attrs = obj_attrs.get('(unknown)', {})
    if unknown_attrs:
        print(f"  WARNING: {len(unknown_attrs)} attribute(s) could not be mapped to an object type:")
        for attr in sorted(unknown_attrs):
            print(f"    {attr}")


if __name__ == '__main__':
    main()
