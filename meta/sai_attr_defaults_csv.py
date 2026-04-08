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
#          their @type, @default, and @flags metadata values.  For enum-typed
#          attributes that carry no explicit @default, the first enumerator of
#          the type is used as the default value.
#
# Usage:   python3 meta/sai_attr_defaults_csv.py
#          (must be run from the repository root, or pass --inc-dir / --output)
#
# Output:  sai_attr_defaults.csv
#          columns: attribute_name, type, default_value, mandatory
#          The "mandatory" column is True when @flags contains
#          MANDATORY_ON_CREATE, False otherwise.
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

# Matches the @type tag inside a Doxygen comment line.
# Group 1 captures everything after "@type " on that line.
_RE_TYPE_TAG = re.compile(r'@type\s+(.+)')

# Matches the @flags tag inside a Doxygen comment line.
# Group 1 captures everything after "@flags " on that line.
_RE_FLAGS_TAG = re.compile(r'@flags\s+(.+)')

# Matches the @default tag inside a Doxygen comment line.
# Group 1 captures everything after "@default " on that line.
_RE_DEFAULT_TAG = re.compile(r'@default\s+(.+)')

# Matches the @flags tag inside a Doxygen comment line.
# Group 1 captures everything after "@flags " on that line.
_RE_FLAGS_TAG = re.compile(r'@flags\s+(.+)')

# Lines that open or close a Doxygen block.
_RE_DOC_OPEN  = re.compile(r'/\*\*')
_RE_DOC_CLOSE = re.compile(r'\*/')

# Matches a "typedef enum _sai_foo_t" opening line; group 1 = internal name.
_RE_ENUM_OPEN = re.compile(r'typedef\s+enum\s+(_sai_\w+)\s*$')

# Matches a "} sai_foo_t;" closing line; group 1 = public typedef name.
_RE_ENUM_CLOSE = re.compile(r'^\s*\}\s*(sai_\w+)\s*;')

# Matches an enumerator line (may have initializer, must not be a comment).
# Group 1 = enumerator name.
_RE_ENUMERATOR = re.compile(r'^\s*(SAI_[A-Z0-9_]+)\s*(?:=\s*[^,/]+)?\s*,')


def build_enum_first_value_map(headers):
    """Return dict mapping each SAI enum typedef name to its first enumerator.

    Scans every header file for  typedef enum _sai_foo_t { ... } sai_foo_t;
    blocks and records the first enumerator (skipping comment lines).
    """

    enum_map = {}   # sai_foo_t -> 'SAI_FOO_FIRST_VALUE'

    for path in headers:
        with open(path, encoding='utf-8', errors='replace') as fh:
            lines = fh.readlines()

        in_enum       = False
        first_value   = None   # first enumerator seen in current block
        in_block_comment = False

        for line in lines:
            stripped = line.strip()

            # Track block comments so we ignore enumerator-like text inside them.
            if not in_block_comment:
                if '/*' in line:
                    in_block_comment = True
                    if '*/' in line:
                        in_block_comment = False
                    continue
            else:
                if '*/' in line:
                    in_block_comment = False
                continue

            if stripped.startswith('//'):
                continue

            if not in_enum:
                if _RE_ENUM_OPEN.search(line):
                    in_enum     = True
                    first_value = None
            else:
                # Look for the closing "} sai_foo_t;" before checking enumerators
                # so a closing line like "} sai_foo_t;" is never mistaken for one.
                m_close = _RE_ENUM_CLOSE.match(line)
                if m_close:
                    typedef_name = m_close.group(1)
                    if first_value is not None:
                        enum_map[typedef_name] = first_value
                    in_enum     = False
                    first_value = None
                elif first_value is None:
                    m_enum = _RE_ENUMERATOR.match(line)
                    if m_enum:
                        first_value = m_enum.group(1)

    return enum_map


def parse_header(path):
    """Return list of (attr_name, type_value, default_value, mandatory) tuples.

    Every SAI_*_ATTR_* enumerator is included.  type_value and default_value
    are empty strings when the corresponding tag is absent from the doc-comment.
    mandatory is True when the @flags tag contains MANDATORY_ON_CREATE.
    Sentinel range-boundary attributes (_START, _END, etc.) are excluded.
    """

    results = []

    with open(path, encoding='utf-8', errors='replace') as fh:
        lines = fh.readlines()

    in_comment = False
    current_type    = None   # @type value seen in the current doc-comment
    current_default = None   # @default value seen in the current doc-comment
    current_flags   = None   # @flags value seen in the current doc-comment
    pending_type    = None   # to attach to the next attribute
    pending_default = None   # to attach to the next attribute
    pending_flags   = None   # to attach to the next attribute

    for line in lines:
        stripped = line.strip()

        if not in_comment:
            if _RE_DOC_OPEN.search(line):
                in_comment      = True
                current_type    = None
                current_flags   = None
                current_default = None
                current_flags   = None
                # Handle single-line /** … */ blocks.
                if _RE_DOC_CLOSE.search(line):
                    in_comment = False
                    mt = _RE_TYPE_TAG.search(line)
                    mf = _RE_FLAGS_TAG.search(line)
                    md = _RE_DEFAULT_TAG.search(line)
                    mf = _RE_FLAGS_TAG.search(line)
                    pending_type    = mt.group(1).strip() if mt else None
                    pending_flags   = mf.group(1).strip() if mf else None
                    pending_default = md.group(1).strip() if md else None
                    pending_flags   = mf.group(1).strip() if mf else None
            else:
                m = _RE_ATTR_NAME.match(line)
                if m:
                    attr = m.group(1)
                    if not _RE_ATTR_SENTINEL.search(attr):
                        flags_str = pending_flags or ''
                        mandatory = 'MANDATORY_ON_CREATE' in flags_str
                        results.append((
                            attr,
                            pending_type    if pending_type    is not None else '',
                            pending_flags   if pending_flags   is not None else '',
                            pending_default if pending_default is not None else '',
                            mandatory,
                        ))
                    pending_type    = None
                    pending_flags   = None
                    pending_default = None
                    pending_flags   = None
                else:
                    # Non-blank, non-comment source line that is not an attribute
                    # resets pending state so we don't carry tags across constructs.
                    if stripped and not stripped.startswith('//'):
                        pending_type    = None
                        pending_flags   = None
                        pending_default = None
                        pending_flags   = None
        else:
            # Inside a /** … */ block – collect tag values.
            mt = _RE_TYPE_TAG.search(line)
            if mt:
                current_type = mt.group(1).strip()

            mf = _RE_FLAGS_TAG.search(line)
            if mf:
                current_flags = mf.group(1).strip()

            md = _RE_DEFAULT_TAG.search(line)
            if md:
                current_default = md.group(1).strip()

            mf = _RE_FLAGS_TAG.search(line)
            if mf:
                current_flags = mf.group(1).strip()

            if _RE_DOC_CLOSE.search(line):
                in_comment      = False
                pending_type    = current_type
                pending_flags   = current_flags
                pending_default = current_default
                pending_flags   = current_flags
                current_type    = None
                current_flags   = None
                current_default = None
                current_flags   = None

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

    enum_first = build_enum_first_value_map(headers)

    all_rows = []
    for hdr in headers:
        rows = parse_header(hdr)
        all_rows.extend(rows)

    # For enum-typed attributes with no @default, fill in the first enumerator.
    # The @type field may be a plain enum name ("sai_foo_t") or a list type
    # ("sai_s32_list_t sai_foo_t").  Only plain enum types get the fallback.
    filled_rows = []
    for attr, type_str, default, mandatory in all_rows:
        if not default and type_str in enum_first:
            default = enum_first[type_str]
        filled_rows.append((attr, type_str, default, mandatory))

    with open(args.output, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['attribute_name', 'type', 'default_value', 'mandatory'])
        writer.writerows(filled_rows)

    with_default  = sum(1 for _, _t, v, _m in filled_rows if v)
    num_mandatory = sum(1 for _, _t, _v, m in filled_rows if m)
    print(f'Written {len(filled_rows)} attributes to {args.output} '
          f'({with_default} with a @default value, '
          f'{num_mandatory} mandatory-on-create, '
          f'{len(filled_rows) - with_default} without default)')


if __name__ == '__main__':
    main()
