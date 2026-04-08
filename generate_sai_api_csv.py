#!/usr/bin/env python3
"""
Generate a CSV file listing all SAI APIs for all SAI objects.

Output format: File, SAI object, SAI API
"""

import csv
import glob
import os
import re

INC_DIR = os.path.join(os.path.dirname(__file__), 'inc')
EXP_DIR = os.path.join(os.path.dirname(__file__), 'experimental')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), 'sai_api_list.csv')

EXCLUDE_OBJECT_TYPE_SUFFIXES = {
    'NULL', 'MAX',
    'EXTENSIONS_RANGE_BASE', 'EXTENSIONS_RANGE_START', 'EXTENSIONS_RANGE_END', 'EXTENSIONS_RANGE_MAX',
    'CUSTOM_RANGE_BASE', 'CUSTOM_RANGE_END', 'CUSTOM_RANGE_MAX',
}

# Functions whose object type cannot be inferred from the function name alone
MANUAL_OBJECT_OVERRIDES = {
    # Service method table — not bound to any specific SAI object
    'sai_profile_get_value_fn':                              'SAI_OBJECT_TYPE_NULL',
    'sai_profile_get_next_value_fn':                         'SAI_OBJECT_TYPE_NULL',
    # Generic bulk helpers defined in saitypes.h
    'sai_bulk_object_create_fn':                             'SAI_OBJECT_TYPE_NULL',
    'sai_bulk_object_remove_fn':                             'SAI_OBJECT_TYPE_NULL',
    'sai_bulk_object_set_attribute_fn':                      'SAI_OBJECT_TYPE_NULL',
    'sai_bulk_object_get_attribute_fn':                      'SAI_OBJECT_TYPE_NULL',
    # Event notifications and bulk operations tied to specific objects
    'sai_fdb_event_notification_fn':                         'SAI_OBJECT_TYPE_FDB_ENTRY',
    'sai_flush_fdb_entries_fn':                              'SAI_OBJECT_TYPE_FDB_ENTRY',
    'sai_packet_event_notification_fn':                      'SAI_OBJECT_TYPE_HOSTIF_PACKET',
    'sai_nat_event_notification_fn':                         'SAI_OBJECT_TYPE_NAT_ENTRY',
    'sai_remove_all_neighbor_entries_fn':                    'SAI_OBJECT_TYPE_NEIGHBOR_ENTRY',
    'sai_flow_bulk_get_session_event_notification_fn':       'SAI_OBJECT_TYPE_FLOW_ENTRY_BULK_GET_SESSION',
}


def collect_object_types(headers):
    """Return a dict mapping lowercase object name to SAI_OBJECT_TYPE_* string."""
    obj_map = {}
    for filepath in headers:
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        for suffix in re.findall(r'\bSAI_OBJECT_TYPE_([A-Z0-9_]+)\b', content):
            if suffix not in EXCLUDE_OBJECT_TYPE_SUFFIXES:
                full = 'SAI_OBJECT_TYPE_' + suffix
                name_lc = suffix.lower()
                obj_map[name_lc] = full
    return obj_map


def infer_object_type(fn_name, sorted_names, obj_map):
    """
    Infer SAI_OBJECT_TYPE_* from a function typedef name like sai_create_port_fn.

    Strategy: strip 'sai_' prefix and '_fn' suffix, then greedily match the
    longest known object name as a whole underscore-delimited token.
    """
    if fn_name in MANUAL_OBJECT_OVERRIDES:
        return MANUAL_OBJECT_OVERRIDES[fn_name]

    inner = fn_name
    if inner.startswith('sai_'):
        inner = inner[4:]
    if inner.endswith('_fn'):
        inner = inner[:-3]

    for name in sorted_names:
        if re.search(r'(^|_)' + re.escape(name) + r'($|_)', inner):
            return obj_map[name]
    return '(unknown)'


def main():
    headers = (
        sorted(glob.glob(os.path.join(INC_DIR, '*.h'))) +
        sorted(glob.glob(os.path.join(EXP_DIR, '*.h')))
    )

    obj_map = collect_object_types(headers)
    # Sort longest-first so greedy matching prefers the most specific object name
    sorted_names = sorted(obj_map.keys(), key=len, reverse=True)

    rows = []
    for filepath in headers:
        rel_path = os.path.relpath(filepath, os.path.dirname(__file__))
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()

        fn_typedefs = re.findall(
            r'typedef\s+\S+\s+\(\*(\bsai_\w+_fn\b)\)\s*\(', content
        )
        for fn_name in fn_typedefs:
            obj_type = infer_object_type(fn_name, sorted_names, obj_map)
            rows.append((rel_path, obj_type, fn_name))

    rows.sort(key=lambda r: (r[0], r[1], r[2]))

    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'SAI object', 'SAI API'])
        writer.writerows(rows)

    print(f"Written {len(rows)} rows to {OUTPUT_CSV}")

    unknown = [r for r in rows if r[1] == '(unknown)']
    if unknown:
        print(f"WARNING: {len(unknown)} entries with unknown object type:")
        for r in unknown:
            print(f"  {r}")


if __name__ == '__main__':
    main()
