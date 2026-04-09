#!/usr/bin/env python3
"""
Combine sai_api_list.csv and sai_attr_defaults.csv into a single JSON file
that maps each SAI object type to its Thrift functions and attribute defaults.

Output format:
{
    "SAI_OBJECT_TYPE_SWITCH": {
        "functions": ["sai_thrift_create_switch", "sai_thrift_get_switch_attribute", ...],
        "attributes": {
            "SAI_SWITCH_ATTR_FOO": "<default_value>",
            ...
        }
    },
    ...
}

Attribute-to-object mapping rule:
    SAI_<OBJECT>_ATTR_<NAME>  ->  SAI_OBJECT_TYPE_<OBJECT>

Functions with an empty "Python Thrift function" column are skipped.
"""

import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_CSV = os.path.join(SCRIPT_DIR, 'sai_api_list.csv')
ATTR_CSV = os.path.join(SCRIPT_DIR, 'sai_attr_defaults.csv')
OUTPUT_JSON = os.path.join(SCRIPT_DIR, 'sai_api_attributes.json')


def load_functions(api_csv):
    """
    Return a dict mapping SAI object type -> sorted list of unique Thrift functions.

    Rows where the "Python Thrift function" column is empty are skipped.
    SAI_OBJECT_TYPE_NULL entries are also skipped.
    """
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
    """
    Derive the SAI object type from an attribute name.

    Convention: SAI_<OBJECT>_ATTR_<FIELD>  ->  SAI_OBJECT_TYPE_<OBJECT>
    """
    marker = '_ATTR_'
    idx = attr_name.find(marker)
    if idx == -1:
        return '(unknown)'
    prefix = attr_name[:idx]           # e.g. "SAI_SWITCH"
    if not prefix.startswith('SAI_'):
        return '(unknown)'
    obj_suffix = prefix[4:]            # e.g. "SWITCH"
    return 'SAI_OBJECT_TYPE_' + obj_suffix


def load_attributes(attr_csv):
    """
    Return a dict mapping SAI object type -> {attribute_name: default_value}.

    The default value is taken verbatim from the CSV; empty strings are preserved.
    """
    obj_attrs: dict[str, dict[str, str]] = {}
    with open(attr_csv, newline='') as f:
        for row in csv.DictReader(f):
            attr_name = row['attribute_name'].strip()
            default = row['default_value'].strip()
            obj_type = attr_to_object_type(attr_name)
            obj_attrs.setdefault(obj_type, {})
            obj_attrs[obj_type][attr_name] = default
    return obj_attrs


def build_combined(obj_functions, obj_attrs):
    """
    Merge functions and attributes into a single dict keyed by SAI object type.

    Object types that appear only in one source are still included so that the
    JSON is complete.
    """
    all_obj_types = sorted(set(obj_functions) | set(obj_attrs))
    combined = {}
    for obj_type in all_obj_types:
        if obj_type == '(unknown)':
            continue
        combined[obj_type] = {
            'functions': obj_functions.get(obj_type, []),
            'attributes': obj_attrs.get(obj_type, {}),
        }
    return combined


def main():
    obj_functions = load_functions(API_CSV)
    obj_attrs = load_attributes(ATTR_CSV)
    combined = build_combined(obj_functions, obj_attrs)

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(combined, f, indent=2)

    print(f"Written {len(combined)} object types to {OUTPUT_JSON}")

    fn_total = sum(len(v['functions']) for v in combined.values())
    attr_total = sum(len(v['attributes']) for v in combined.values())
    print(f"  {fn_total} Thrift functions")
    print(f"  {attr_total} attributes with default values")

    unknown_attrs = obj_attrs.get('(unknown)', {})
    if unknown_attrs:
        print(f"  WARNING: {len(unknown_attrs)} attribute(s) could not be mapped to an object type:")
        for attr in sorted(unknown_attrs):
            print(f"    {attr}")


if __name__ == '__main__':
    main()
