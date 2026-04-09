#!/usr/bin/env python3
"""
Combine sai_api_list.csv and sai_attr_defaults.csv into:

  1. sai_api_attributes.json        -- full combined JSON (all object types)
  2. sai_data/<stem>_api_attributes.json
                                    -- one JSON per SAI header file
                                       (e.g. sai_data/saivlan_api_attributes.json)
  3. ptf/<stem>_test.py             -- thin PTF test module per header, each
                                       containing a single test class that
                                       inherits SaiApiTestBase and points at the
                                       matching per-header JSON.

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
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INC_DIR = os.path.join(SCRIPT_DIR, 'inc')
API_CSV = os.path.join(SCRIPT_DIR, 'sai_api_list.csv')
ATTR_CSV = os.path.join(SCRIPT_DIR, 'sai_attr_defaults.csv')
OUTPUT_JSON = os.path.join(SCRIPT_DIR, 'sai_api_attributes.json')
SAI_DATA_DIR = os.path.join(SCRIPT_DIR, 'sai_data')
PTF_DIR = os.path.join(SCRIPT_DIR, 'ptf', 'unittests')


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def load_functions(api_csv):
    """
    Return:
      obj_functions  -- dict: SAI object type -> sorted list of unique Thrift functions
      hdr_to_objs    -- dict: header stem (e.g. 'saivlan') -> sorted list of object types
    """
    obj_functions: dict[str, list[str]] = {}
    hdr_to_objs: dict[str, list[str]] = {}

    with open(api_csv, newline='') as f:
        for row in csv.DictReader(f):
            obj_type = row['SAI object'].strip()
            thrift_fn = row['Python Thrift function'].strip()
            header = row['File'].strip()            # e.g. inc/saivlan.h
            stem = os.path.basename(header).replace('.h', '')  # e.g. saivlan

            if obj_type == 'SAI_OBJECT_TYPE_NULL':
                continue

            # Track header -> object mapping regardless of thrift_fn presence
            if stem not in hdr_to_objs:
                hdr_to_objs[stem] = []
            if obj_type not in hdr_to_objs[stem]:
                hdr_to_objs[stem].append(obj_type)

            if not thrift_fn:
                continue

            obj_functions.setdefault(obj_type, [])
            if thrift_fn not in obj_functions[obj_type]:
                obj_functions[obj_type].append(thrift_fn)

    for obj_type in obj_functions:
        obj_functions[obj_type].sort()
    for stem in hdr_to_objs:
        hdr_to_objs[stem].sort()

    return obj_functions, hdr_to_objs


def attr_to_object_type(attr_name: str) -> str:
    """Derive SAI_OBJECT_TYPE_<X> from SAI_<X>_ATTR_<FIELD>."""
    idx = attr_name.find('_ATTR_')
    if idx == -1 or not attr_name.startswith('SAI_'):
        return '(unknown)'
    return 'SAI_OBJECT_TYPE_' + attr_name[4:idx]


def load_attributes(attr_csv):
    """
    Return dict: SAI object type -> {attr_name: {'type': ..., 'default_value': ...}}.

    Supports both the old CSV column names (attribute_name / type / default_value)
    and the updated names (Attribute name / Type / Default value).
    """
    obj_attrs: dict[str, dict] = {}
    with open(attr_csv, newline='') as f:
        reader = csv.DictReader(f)
        # Normalise column names to lowercase with underscores
        headers = {h: h.strip().lower().replace(' ', '_') for h in reader.fieldnames or []}
        for row in reader:
            row = {headers[k]: v.strip() for k, v in row.items()}
            attr_name = row.get('attribute_name', '')
            attr_type = row.get('type', '')
            default   = row.get('default_value', '')
            obj_type  = attr_to_object_type(attr_name)
            obj_attrs.setdefault(obj_type, {})
            obj_attrs[obj_type][attr_name] = {
                'type':          attr_type,
                'default_value': default,
            }
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
    Merge functions and attributes (with annotation metadata), keyed by object type.

    Every attribute entry has the structure:
        {
            "type":      "<SAI type string>",
            "def_value": "<default value string>",
            ["condition": [...]]   # only when @condition is present in the header
        }

    @validonly annotations are intentionally excluded from the output.
    """
    all_obj_types = sorted(set(obj_functions) | set(obj_attrs))
    combined = {}
    for obj_type in all_obj_types:
        if obj_type == '(unknown)':
            continue

        attrs_raw = obj_attrs.get(obj_type, {})
        attrs_out = {}
        for attr_name, attr_data in attrs_raw.items():
            attr_type     = attr_data.get('type', '')
            default_val   = attr_data.get('default_value', '')
            ann           = annotations.get(attr_name)

            entry: dict = {
                'type':      attr_type,
                'def_value': default_val,
            }

            # Include @condition but NOT @validonly
            if ann and 'condition' in ann:
                entry['condition'] = ann['condition']

            attrs_out[attr_name] = entry

        combined[obj_type] = {
            'functions': obj_functions.get(obj_type, []),
            'attributes': attrs_out,
        }
    return combined


# ---------------------------------------------------------------------------
# Per-header JSON splitter
# ---------------------------------------------------------------------------

def split_by_header(combined: dict, hdr_to_objs: dict, out_dir: str) -> dict[str, str]:
    """
    Write one JSON file per SAI header into out_dir.

    Returns a dict mapping header stem -> output file path.
    """
    os.makedirs(out_dir, exist_ok=True)
    stem_to_path: dict[str, str] = {}

    for stem, obj_types in sorted(hdr_to_objs.items()):
        subset = {ot: combined[ot] for ot in obj_types if ot in combined}
        if not subset:
            continue
        filename = f"{stem}_api_attributes.json"
        out_path = os.path.join(out_dir, filename)
        with open(out_path, 'w') as f:
            json.dump(subset, f, indent=2)
        stem_to_path[stem] = out_path

    return stem_to_path


# ---------------------------------------------------------------------------
# Per-header PTF test file generator
# ---------------------------------------------------------------------------

def _stem_to_class_name(stem: str) -> str:
    """saivlan -> SaiVlanTest,  saiacl -> SaiAclTest"""
    # strip leading 'sai', capitalise remaining words split on known boundaries
    without_sai = stem[3:] if stem.startswith('sai') else stem
    # insert word boundaries before sequences that look like a new word
    # (upper-case transitions are already absent in stems; just capitalise whole thing)
    return 'Sai' + without_sai.capitalize() + 'Test'


_PTF_TEST_TEMPLATE = '''\
"""
Auto-generated PTF test for {header}.

Validates all SAI object types defined in {header}:
{object_list}

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', '{json_filename}',
)


class {class_name}(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in {header}:
{object_doclist}
    """

    json_path = _JSON
    object_types = {object_types_repr}
'''


def generate_ptf_tests(stem_to_path: dict, hdr_to_objs: dict, ptf_dir: str) -> list[str]:
    """
    Write one PTF test module per header stem into ptf_dir.
    Also writes run_tests.sh with the PTF command for each test.
    Returns the list of generated test file paths.
    """
    os.makedirs(ptf_dir, exist_ok=True)
    generated = []
    run_lines = []

    PTF_CMD = (
        "./SAI/test/ptf/ptf"
        " --test-dir SAI/ptf/unittests"
        " --test-params=\"port_map_file='config/ptf_port_map.ini'\""
    )

    for stem, json_path in sorted(stem_to_path.items()):
        obj_types = hdr_to_objs.get(stem, [])
        header = f"inc/{stem}.h"
        json_filename = os.path.basename(json_path)
        class_name = _stem_to_class_name(stem)

        object_list = '\n'.join(f'  - {ot}' for ot in obj_types)
        object_doclist = '\n'.join(f'        {ot}' for ot in obj_types)
        object_types_repr = repr(obj_types)

        src = _PTF_TEST_TEMPLATE.format(
            header=header,
            json_filename=json_filename,
            class_name=class_name,
            object_list=object_list,
            object_doclist=object_doclist,
            object_types_repr=object_types_repr,
        )

        out_path = os.path.join(ptf_dir, f"{stem}_test.py")
        with open(out_path, 'w') as f:
            f.write(src)
        generated.append(out_path)
        run_lines.append(f"{PTF_CMD} {stem}_test.{class_name}")

    # Write run_tests.sh
    run_script = os.path.join(ptf_dir, 'run_tests.sh')
    with open(run_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('# Auto-generated list of PTF test commands for all SAI API unit tests.\n')
        f.write('# Each line runs one per-header test class against a live SAI device.\n')
        f.write('#\n')
        f.write('# Usage:\n')
        f.write('#   cd <repo-root>\n')
        f.write('#   bash ptf/unittests/run_tests.sh\n')
        f.write('#\n')
        f.write('# Or execute individual lines directly.\n\n')
        f.write('\n'.join(run_lines) + '\n')

    return generated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    obj_functions, hdr_to_objs = load_functions(API_CSV)
    obj_attrs = load_attributes(ATTR_CSV)
    annotations = parse_header_annotations(INC_DIR)

    combined = build_combined(obj_functions, obj_attrs, annotations)

    # 1. Write the full combined JSON
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(combined, f, indent=2)

    with_condition = sum(
        1
        for obj_data in combined.values()
        for v in obj_data['attributes'].values()
        if 'condition' in v
    )
    fn_total   = sum(len(v['functions'])  for v in combined.values())
    attr_total = sum(len(v['attributes']) for v in combined.values())

    print(f"Written {len(combined)} object types to {OUTPUT_JSON}")
    print(f"  {fn_total} Thrift functions, {attr_total} attributes "
          f"({with_condition} with @condition)")

    unknown_attrs = obj_attrs.get('(unknown)', {})
    if unknown_attrs:
        print(f"  WARNING: {len(unknown_attrs)} attribute(s) could not be mapped "
              f"to an object type:")
        for attr in sorted(unknown_attrs):
            print(f"    {attr}")

    print(f"\n  Note: @validonly annotations excluded from output (use @condition only)")

    # 2. Write per-header JSON files
    stem_to_path = split_by_header(combined, hdr_to_objs, SAI_DATA_DIR)
    print(f"\nWritten {len(stem_to_path)} per-header JSON files to {SAI_DATA_DIR}/")

    # 3. Write per-header PTF test files
    generated = generate_ptf_tests(stem_to_path, hdr_to_objs, PTF_DIR)
    print(f"Written {len(generated)} per-header PTF test files to {PTF_DIR}/")


if __name__ == '__main__':
    main()
