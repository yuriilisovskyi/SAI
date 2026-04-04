#!/usr/bin/env python3
#
# Copyright (c) 2014 Microsoft Open Technologies, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#    THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
#    CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
#    LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
#    FOR A PARTICULAR PURPOSE, MERCHANTABILITY OR NON-INFRINGEMENT.
#
#    See the Apache Version 2.0 License for specific language governing
#    permissions and limitations under the License.
#
#    Microsoft would like to thank the following companies for their review and
#    assistance with these files: Intel Corporation, Mellanox Technologies Ltd,
#    Dell Products, L.P., Facebook, Inc., Marvell International Ltd.
#
# @file    sai_attr_defaults_csv.py
#
# @brief   Parses SAI headers in inc/ and emits a CSV of attribute names with
#          their @default metadata values.
#
# Usage:   python3 meta/sai_attr_defaults_csv.py
#          (must be run from the repository root, or pass --inc-dir / --output)
#
# Output:  sai_attr_defaults.csv   (two columns: attribute_name, default_value)
#

import argparse
import csv
import glob
import os
import re
import sys


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

# Matches a SAI attribute identifier on its own source line, optionally with
# an initialiser (= SAI_*_START or = 0x…) and an optional trailing comma.
# Group 1 captures the attribute name.
_RE_ATTR_NAME = re.compile(
    r'^\s*(SAI_\w+_ATTR_\w+)\s*(?:=\s*[^,]+)?\s*,?\s*$'
)

# Sentinel / range-boundary attributes that are not real attributes:
# anything ending with _START, _END, _CUSTOM_RANGE_START, or _CUSTOM_RANGE_END.
_RE_ATTR_SENTINEL = re.compile(
    r'(?:_CUSTOM_RANGE)?_(?:START|END)$'
)

# Matches the @default tag inside a Doxygen comment line.
# Group 1 captures everything after "@default " on that line.
_RE_DEFAULT_TAG = re.compile(r'@default\s+(.+)')

# Lines that open or close a Doxygen block.
_RE_DOC_OPEN  = re.compile(r'/\*\*')
_RE_DOC_CLOSE = re.compile(r'\*/')


def parse_header(path):
    """Return list of (attr_name, default_value) tuples from one header file.

    Every SAI_*_ATTR_* enumerator is included.  default_value is an empty
    string when the attribute has no @default tag.
    """

    results = []

    with open(path, encoding='utf-8', errors='replace') as fh:
        lines = fh.readlines()

    in_comment = False
    current_default = None   # @default value seen in the current doc-comment
    pending_default = None   # default to attach to the next attribute (None = not set)

    for line in lines:
        stripped = line.strip()

        # --- comment block tracking ---
        if not in_comment:
            if _RE_DOC_OPEN.search(line):
                in_comment = True
                current_default = None
                # Check whether open and close are on the same line
                # (single-line /** … */ block) – uncommon but possible.
                if _RE_DOC_CLOSE.search(line):
                    in_comment = False
                    m = _RE_DEFAULT_TAG.search(line)
                    pending_default = m.group(1).strip() if m else None
            else:
                # Outside a comment – look for an attribute enumerator.
                m = _RE_ATTR_NAME.match(line)
                if m:
                    attr = m.group(1)
                    if _RE_ATTR_SENTINEL.search(attr):
                        pending_default = None
                    else:
                        # Always emit the attribute; use empty string when there is
                        # no @default in the preceding doc-comment.
                        results.append((attr, pending_default if pending_default is not None else ''))
                        pending_default = None
                else:
                    # Any non-blank, non-comment source line that is NOT an
                    # attribute resets the pending default so we don't carry
                    # a default across unrelated constructs.
                    if stripped and not stripped.startswith('//'):
                        pending_default = None
        else:
            # Inside a /** … */ block
            m = _RE_DEFAULT_TAG.search(line)
            if m:
                current_default = m.group(1).strip()

            if _RE_DOC_CLOSE.search(line):
                in_comment = False
                pending_default = current_default
                current_default = None

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Generate CSV of SAI attributes and their @default values.'
    )
    parser.add_argument(
        '--inc-dir',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'inc'),
        help='Path to the inc/ directory (default: ../inc relative to this script)',
    )
    parser.add_argument(
        '--output',
        default='sai_attr_defaults.csv',
        help='Output CSV file path (default: sai_attr_defaults.csv)',
    )
    args = parser.parse_args()

    inc_dir = os.path.realpath(args.inc_dir)
    if not os.path.isdir(inc_dir):
        sys.exit(f'ERROR: inc directory not found: {inc_dir}')

    headers = sorted(glob.glob(os.path.join(inc_dir, 'sai*.h')))
    if not headers:
        sys.exit(f'ERROR: no sai*.h files found in {inc_dir}')

    all_rows = []
    for hdr in headers:
        rows = parse_header(hdr)
        all_rows.extend(rows)

    with open(args.output, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['attribute_name', 'default_value'])
        writer.writerows(all_rows)

    with_default = sum(1 for _, v in all_rows if v)
    print(f'Written {len(all_rows)} attributes to {args.output} '
          f'({with_default} with a @default value, '
          f'{len(all_rows) - with_default} without)')


if __name__ == '__main__':
    main()
