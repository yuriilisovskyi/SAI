# Copyright 2021-present Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SAI PTFv2 Unit Tests for ACL Feature

Validates the SAI ACL implementation by:
  1. Discovering all SAI ACL APIs and attribute constants from
     test/saithriftv2/build/lib/sai_thrift (sai_adapter + sai_headers).
  2. Verifying that each CRUD API call with default values returns
     SAI_STATUS_SUCCESS against a running SAI implementation.
  3. For get calls: iterating over ALL attributes defined in
     sai_attr_defaults.csv for the object type and comparing each
     returned value against the default specified in that CSV.

Each test class inherits from ThriftInterface (ptf/sai_base_test.py) which
sets up the Thrift RPC connection via setUp/tearDown.  Each class defines a
runTest method that calls create, get, set (where applicable), and remove
helper methods in sequence using a single SAI object.

Note: set_acl_table_group_attribute, set_acl_table_attribute, and
set_acl_range_attribute are omitted because all attributes for those object
types are CREATE_ONLY in the SAI spec; the generated adapter functions return
SAI_STATUS_NOT_SUPPORTED by design and there is nothing to set.

Prerequisites:
  1. Build the sai_thrift package:
       export SAITHRIFTV2=y
       make saithrift-build        # from the repo root
       cd test/saithriftv2 && python3 setup.py install

  2. Start the SAI RPC server (saiserver) with a SAI library loaded.

Run with:
    ptf --test-dir ptf/utest sai_acl_unit_test
or:
    python3 -m pytest ptf/utest/sai_acl_unit_test.py -v
"""

import csv
import glob
import inspect
import os
import sys
import xml.etree.ElementTree as ET

from sai_base_test import ThriftInterface

# All SAI API functions, type helpers, and attribute constants are imported
# directly from the generated sai_thrift package (no embedded stubs).
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter

# ---------------------------------------------------------------------------
# Mandatory-on-create attribute discovery via SAI metadata XML
# ---------------------------------------------------------------------------

# Path to the doxygen-generated XML produced by 'make xml' in meta/.
_XML_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "meta", "xml",
)


def get_mandatory_on_create_attrs(object_type_name, xml_dir=_XML_DIR):
    """
    Return a list of attribute constant names (strings) that are marked
    MANDATORY_ON_CREATE for the SAI object type identified by
    *object_type_name*.

    The function discovers mandatory attributes by inspecting the doxygen XML
    files generated from the SAI headers (``meta/xml/group__SAI*.xml``).
    Each enumvalue element whose ``detaileddescription`` contains the text
    "MANDATORY_ON_CREATE" is collected and its ``name`` text is returned.

    Args:
        object_type_name (str): SAI object type name without the
            ``SAI_OBJECT_TYPE_`` prefix, e.g. ``"ACL_TABLE_GROUP"`` or
            ``"ACL_ENTRY"``.  The prefix ``SAI_`` is prepended to build the
            expected attribute name prefix ``SAI_<object_type_name>_ATTR_``.
        xml_dir (str): Path to the directory containing doxygen XML files.
            Defaults to ``meta/xml/`` relative to the repository root.

    Returns:
        list[str]: Sorted list of attribute constant names whose
        ``sai_thrift_attr_metadata_t.ismandatoryoncreate`` is True,
        e.g. ``["SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE"]``.

    Example::

        mandatory = get_mandatory_on_create_attrs("ACL_TABLE_GROUP")
        # ["SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE"]

        mandatory = get_mandatory_on_create_attrs("ACL_TABLE_GROUP_MEMBER")
        # ["SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_GROUP_ID",
        #  "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_ID",
        #  "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_PRIORITY"]
    """
    attr_prefix = "SAI_{}_ATTR_".format(object_type_name)
    mandatory = []

    for xml_file in glob.glob(os.path.join(xml_dir, "group__SAI*.xml")):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        xml_text = ET.tostring(root, encoding="unicode")

        # Quick pre-filter: skip files that don't mention this attr prefix
        if attr_prefix not in xml_text:
            continue

        # Walk every enumvalue element looking for MANDATORY_ON_CREATE
        for enumvalue in root.iter("enumvalue"):
            name_el = enumvalue.find("name")
            if name_el is None or not (name_el.text or "").startswith(attr_prefix):
                continue
            detail_el = enumvalue.find("detaileddescription")
            if detail_el is None:
                continue
            detail_text = ET.tostring(detail_el, encoding="unicode")
            if "MANDATORY_ON_CREATE" in detail_text:
                mandatory.append(name_el.text)

    return sorted(set(mandatory))


# Path to the SAI attribute defaults CSV (repo root).
_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sai_attr_defaults.csv",
)


# ---------------------------------------------------------------------------
# CSV loader – reads sai_attr_defaults.csv once at import time
# ---------------------------------------------------------------------------

def _load_attr_defaults(csv_path):
    """
    Parse sai_attr_defaults.csv and return a dict:
        { attribute_name: (type_str, default_str) }

    Rows with an empty default_value are included with default_str = "".
    """
    defaults = {}
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            defaults[row["attribute_name"]] = (
                row["type"],
                row["default_value"],
            )
    return defaults


_ATTR_DEFAULTS = _load_attr_defaults(_CSV_PATH)


def _get_object_defaults(attr_prefix):
    """
    Return {attr_name: (type_str, default_str)} for all attributes whose
    name starts with *attr_prefix* (e.g. "SAI_ACL_TABLE_GROUP_ATTR_").
    """
    return {
        name: val
        for name, val in _ATTR_DEFAULTS.items()
        if name.startswith(attr_prefix)
    }


# ---------------------------------------------------------------------------
# Default-value comparator
# ---------------------------------------------------------------------------

def _check_default(test_case, attr_name, type_str, default_str, actual):
    """
    Compare *actual* (the value returned by a sai_thrift get call, keyed by
    the full attribute constant name) against the *default_str* from the CSV.

    Attribute types and their default representations:

      bool            "true" / "false"        → Python bool
      sai_uint*_t     numeric string           → int (u32, u64 …)
      sai_int*_t      numeric string           → int
      sai_*_t (enum)  constant name string     → compare via sai_headers constant
      sai_object_id_t "SAI_NULL_OBJECT_ID" /""→ int 0 or skip
      sai_object_list_t / sai_s32_list_t  "empty" → count == 0
      sai_acl_field_data_t  "disabled"         → enable == False
      sai_acl_action_data_t "disabled"         → enable == False
      sai_u32_range_t   no canonical default   → skip
      char            '""""""'                 → empty string
      (empty string)                           → skip (no default specified)
    """
    if default_str == "":
        # No default defined in CSV – skip value comparison.
        return

    # ---- bool -------------------------------------------------------
    if type_str == "bool":
        expected = default_str.lower() == "true"
        test_case.assertEqual(
            actual, expected,
            "{}: expected bool {}, got {}".format(attr_name, expected, actual),
        )
        return

    # ---- integer scalar types ---------------------------------------
    int_types = {
        "sai_uint8_t", "sai_uint16_t", "sai_uint32_t", "sai_uint64_t",
        "sai_int8_t",  "sai_int16_t",  "sai_int32_t",  "sai_int64_t",
    }
    if type_str in int_types:
        expected = int(default_str)
        test_case.assertEqual(
            actual, expected,
            "{}: expected int {}, got {}".format(attr_name, expected, actual),
        )
        return

    # ---- object id --------------------------------------------------
    if type_str == "sai_object_id_t":
        if default_str == "SAI_NULL_OBJECT_ID":
            test_case.assertEqual(
                actual, SAI_NULL_OBJECT_ID,
                "{}: expected SAI_NULL_OBJECT_ID, got {}".format(attr_name, actual),
            )
        # other OID defaults (e.g. mandatory attrs with no default) – skip
        return

    # ---- enum / s32 -------------------------------------------------
    enum_types = {
        "sai_acl_stage_t",
        "sai_acl_table_group_type_t",
        "sai_acl_table_chain_group_type_t",
        "sai_acl_table_chain_group_stage_t",
        "sai_acl_range_type_t",
        "sai_acl_table_match_type_t",
    }
    if type_str in enum_types:
        expected = globals().get(default_str)
        if expected is None:
            return  # constant not available in this build – skip
        test_case.assertEqual(
            actual, expected,
            "{}: expected {} ({}), got {}".format(attr_name, default_str, repr(expected), repr(actual)),
        )
        return

    # ---- list types -------------------------------------------------
    list_types = {
        "sai_object_list_t",
        "sai_s32_list_t sai_acl_bind_point_type_t",
        "sai_s32_list_t sai_acl_action_type_t",
        "sai_s32_list_t sai_acl_range_type_t",
    }
    if type_str in list_types and default_str == "empty":
        test_case.assertEqual(
            actual.count, 0,
            "{}: expected empty list (count=0), got count={}".format(
                attr_name, actual.count
            ),
        )
        return

    # ---- acl_field_data_t / acl_action_data_t – "disabled" default --
    if default_str == "disabled":
        if actual is not None:
            test_case.assertFalse(
                actual.enable,
                "{}: expected disabled (enable=False), got enable={}".format(
                    attr_name, actual.enable
                ),
            )
        return

    # ---- char (string) ----------------------------------------------
    if type_str == "char":
        expected = ""
        if default_str not in ('""""""', '""'):
            expected = default_str.strip('"')
        if actual is not None:
            test_case.assertEqual(
                actual, expected,
                "{}: expected string '{}', got '{}'".format(attr_name, expected, actual),
            )
        return

    # All other types (sai_u32_range_t etc.) – skip value comparison.


def _verify_object_attributes(test_case, get_fn, oid, attr_prefix, **get_kwargs):
    """
    Call *get_fn* requesting every attribute for *attr_prefix*, then compare
    each returned value against the CSV default via _check_default.

    *get_kwargs* can supply any extra arguments the get function requires
    (e.g. pre-allocated list objects for list-typed attributes).

    Attributes with no corresponding get kwarg in the adapter signature are
    silently skipped.

    Returns the full attrs dict returned by the get function.
    """
    object_defaults = _get_object_defaults(attr_prefix)

    # Build the keyword arguments for the get call – one True per attribute
    # that appears in both the CSV and the adapter function signature.
    import sai_thrift.sai_adapter as _adapter_mod
    sig = inspect.signature(get_fn)
    adapter_params = set(sig.parameters.keys()) - {"client", attr_prefix.rstrip("_").lower()}

    request_kwargs = {}
    for attr_name in object_defaults:
        # Derive the kwarg name from the attribute constant:
        # SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE  →  acl_stage
        # Strip the prefix and lowercase.
        kwarg = attr_name[len(attr_prefix):].lower()
        if kwarg in sig.parameters:
            request_kwargs[kwarg] = True

    # Merge any caller-supplied kwargs (e.g. pre-sized lists).
    request_kwargs.update(get_kwargs)

    attrs = get_fn(test_case.client, oid, **request_kwargs)
    test_case._assert_status_success(adapter.status)

    if attrs is None:
        return attrs

    # Compare each returned value against CSV default.
    for attr_name, (type_str, default_str) in object_defaults.items():
        if attr_name in attrs:
            _check_default(test_case, attr_name, type_str, default_str,
                           attrs[attr_name])

    return attrs


# ---------------------------------------------------------------------------
# Helpers to introspect SAI ACL APIs and attributes at test time
# ---------------------------------------------------------------------------

def _get_acl_api_functions():
    """
    Return a sorted list of (name, callable) tuples for every ACL-related
    function exported by sai_thrift.sai_adapter.
    """
    import sai_thrift.sai_adapter as _mod
    return sorted(
        [
            (name, obj)
            for name, obj in inspect.getmembers(_mod, inspect.isfunction)
            if name.startswith("sai_thrift_") and "_acl_" in name
        ]
    )


def _get_acl_attribute_constants():
    """
    Return {name: value} for every ACL attribute constant visible in this
    module's global namespace after the wildcard imports above.
    """
    current_module = sys.modules[__name__]
    prefixes = (
        "SAI_ACL_TABLE_ATTR_",
        "SAI_ACL_ENTRY_ATTR_",
        "SAI_ACL_COUNTER_ATTR_",
        "SAI_ACL_RANGE_ATTR_",
        "SAI_ACL_TABLE_GROUP_ATTR_",
        "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_",
        "SAI_ACL_TABLE_CHAIN_GROUP_ATTR_",
    )
    return {
        name: getattr(current_module, name)
        for name in dir(current_module)
        if any(name.startswith(p) for p in prefixes)
    }


# ---------------------------------------------------------------------------
# Shared status assertion mixin
# ---------------------------------------------------------------------------

class _SaiAclAssertMixin:
    def _assert_status_success(self, status, msg=""):
        self.assertEqual(
            status,
            SAI_STATUS_SUCCESS,
            msg or "Expected SAI_STATUS_SUCCESS (0), got {}".format(status),
        )


# ===========================================================================
# Test Class 1: Discover ACL APIs and attributes from sai_thrift
# ===========================================================================

class TestAclApiDiscovery(ThriftInterface):
    """
    Verifies that sai_thrift exposes the expected set of SAI ACL API functions
    and attribute constants (sourced from test/saithriftv2/build/lib/sai_thrift).
    """

    EXPECTED_ACL_FUNCTIONS = [
        "sai_thrift_create_acl_table_group",
        "sai_thrift_remove_acl_table_group",
        "sai_thrift_set_acl_table_group_attribute",
        "sai_thrift_get_acl_table_group_attribute",
        "sai_thrift_create_acl_table_group_member",
        "sai_thrift_remove_acl_table_group_member",
        "sai_thrift_set_acl_table_group_member_attribute",
        "sai_thrift_get_acl_table_group_member_attribute",
        "sai_thrift_create_acl_table",
        "sai_thrift_remove_acl_table",
        "sai_thrift_set_acl_table_attribute",
        "sai_thrift_get_acl_table_attribute",
        "sai_thrift_create_acl_entry",
        "sai_thrift_remove_acl_entry",
        "sai_thrift_set_acl_entry_attribute",
        "sai_thrift_get_acl_entry_attribute",
        "sai_thrift_create_acl_counter",
        "sai_thrift_remove_acl_counter",
        "sai_thrift_set_acl_counter_attribute",
        "sai_thrift_get_acl_counter_attribute",
        "sai_thrift_create_acl_range",
        "sai_thrift_remove_acl_range",
        "sai_thrift_set_acl_range_attribute",
        "sai_thrift_get_acl_range_attribute",
    ]

    EXPECTED_ATTR_PREFIXES = [
        "SAI_ACL_TABLE_GROUP_ATTR_",
        "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_",
        "SAI_ACL_TABLE_ATTR_",
        "SAI_ACL_ENTRY_ATTR_",
        "SAI_ACL_COUNTER_ATTR_",
        "SAI_ACL_RANGE_ATTR_",
    ]

    def runTest(self):
        self.verify_acl_api_functions()
        self.verify_acl_attribute_constants()

    def verify_acl_api_functions(self):
        """All expected ACL CRUD functions must be present in sai_thrift.sai_adapter."""
        discovered = {name for name, _ in _get_acl_api_functions()}
        for func_name in self.EXPECTED_ACL_FUNCTIONS:
            self.assertIn(
                func_name,
                discovered,
                "ACL API function '{}' not found in sai_thrift.sai_adapter. "
                "Discovered ACL functions: {}".format(func_name, sorted(discovered)),
            )

    def verify_acl_attribute_constants(self):
        """At least one attribute constant must exist per expected prefix."""
        constants = _get_acl_attribute_constants()
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            matching = [k for k in constants if k.startswith(prefix)]
            self.assertTrue(
                len(matching) > 0,
                "No attribute constants with prefix '{}' found in "
                "sai_thrift.sai_headers. Available ACL constants: {}".format(
                    prefix, sorted(constants.keys())
                ),
            )


# ===========================================================================
# Test Class 2: ACL Table Group CRUD
# ===========================================================================

class TestAclTableGroupCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / remove for ACL Table Group.
    get iterates all SAI_ACL_TABLE_GROUP_ATTR_* attributes from
    sai_attr_defaults.csv and validates each returned value against its
    defined default.
    """

    def runTest(self):
        acl_table_group = self.create_acl_table_group()
        self.get_acl_table_group_attribute(acl_table_group)
        self.remove_acl_table_group(acl_table_group)

    def create_acl_table_group(self):
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
        )
        self._assert_status_success(adapter.status)
        return acl_table_group

    def get_acl_table_group_attribute(self, acl_table_group):
        _verify_object_attributes(
            self,
            sai_thrift_get_acl_table_group_attribute,
            acl_table_group,
            "SAI_ACL_TABLE_GROUP_ATTR_",
        )

    def remove_acl_table_group(self, acl_table_group):
        status = sai_thrift_remove_acl_table_group(self.client, acl_table_group)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 3: ACL Table CRUD
# ===========================================================================

class TestAclTableCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / remove for ACL Table.
    get iterates all SAI_ACL_TABLE_ATTR_* attributes from
    sai_attr_defaults.csv and validates each returned value against its
    defined default.
    """

    def runTest(self):
        acl_table = self.create_acl_table()
        self.get_acl_table_attribute(acl_table)
        self.remove_acl_table(acl_table)

    def create_acl_table(self):
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            field_src_ip=True,
        )
        self._assert_status_success(adapter.status)
        return acl_table

    def get_acl_table_attribute(self, acl_table):
        _verify_object_attributes(
            self,
            sai_thrift_get_acl_table_attribute,
            acl_table,
            "SAI_ACL_TABLE_ATTR_",
        )

    def remove_acl_table(self, acl_table):
        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 4: ACL Table Group Member CRUD
# ===========================================================================

class TestAclTableGroupMemberCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / set / remove for ACL Table Group Member.
    get iterates all SAI_ACL_TABLE_GROUP_MEMBER_ATTR_* attributes from
    sai_attr_defaults.csv and validates each returned value against its
    defined default.
    """

    def runTest(self):
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

        member = self.create_acl_table_group_member(acl_table_group, acl_table)
        self.get_acl_table_group_member_attribute(member)
        self.set_acl_table_group_member_attribute(member)
        self.remove_acl_table_group_member(member)

        sai_thrift_remove_acl_table(self.client, acl_table)
        sai_thrift_remove_acl_table_group(self.client, acl_table_group)

    def create_acl_table_group_member(self, acl_table_group, acl_table):
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=acl_table_group,
            acl_table_id=acl_table,
            priority=10,
        )
        self._assert_status_success(adapter.status)
        return member

    def get_acl_table_group_member_attribute(self, member):
        _verify_object_attributes(
            self,
            sai_thrift_get_acl_table_group_member_attribute,
            member,
            "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_",
        )

    def set_acl_table_group_member_attribute(self, member):
        status = sai_thrift_set_acl_table_group_member_attribute(
            self.client, member
        )
        self._assert_status_success(status)

    def remove_acl_table_group_member(self, member):
        status = sai_thrift_remove_acl_table_group_member(self.client, member)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 5: ACL Entry CRUD
# ===========================================================================

class TestAclEntryCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / set / remove for ACL Entry.
    get iterates all SAI_ACL_ENTRY_ATTR_* attributes from
    sai_attr_defaults.csv and validates each returned value against its
    defined default.
    """

    def runTest(self):
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

        acl_entry = self.create_acl_entry(acl_table)
        self.get_acl_entry_attribute(acl_entry)
        self.set_acl_entry_attribute(acl_entry)
        self.remove_acl_entry(acl_entry)

        sai_thrift_remove_acl_table(self.client, acl_table)

    def create_acl_entry(self, acl_table):
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=acl_table,
            field_src_ip=sai_thrift_acl_field_data_t(
                enable=True,
                data=sai_thrift_acl_field_data_data_t(ip4="10.0.0.1"),
                mask=sai_thrift_acl_field_data_mask_t(ip4="255.255.255.255"),
            ),
            action_packet_action=sai_thrift_acl_action_data_t(
                enable=True,
                parameter=sai_thrift_acl_action_parameter_t(
                    s32=SAI_PACKET_ACTION_DROP
                ),
            ),
        )
        self._assert_status_success(adapter.status)
        return acl_entry

    def get_acl_entry_attribute(self, acl_entry):
        _verify_object_attributes(
            self,
            sai_thrift_get_acl_entry_attribute,
            acl_entry,
            "SAI_ACL_ENTRY_ATTR_",
        )

    def set_acl_entry_attribute(self, acl_entry):
        status = sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, priority=20
        )
        self._assert_status_success(status)

    def remove_acl_entry(self, acl_entry):
        status = sai_thrift_remove_acl_entry(self.client, acl_entry)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 6: ACL Counter CRUD
# ===========================================================================

class TestAclCounterCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / set / remove for ACL Counter.
    get iterates all SAI_ACL_COUNTER_ATTR_* attributes from
    sai_attr_defaults.csv and validates each returned value against its
    defined default.
    """

    def runTest(self):
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

        acl_counter = self.create_acl_counter(acl_table)
        self.get_acl_counter_attribute(acl_counter)
        self.set_acl_counter_attribute(acl_counter)
        self.remove_acl_counter(acl_counter)

        sai_thrift_remove_acl_table(self.client, acl_table)

    def create_acl_counter(self, acl_table):
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=acl_table
        )
        self._assert_status_success(adapter.status)
        return acl_counter

    def get_acl_counter_attribute(self, acl_counter):
        _verify_object_attributes(
            self,
            sai_thrift_get_acl_counter_attribute,
            acl_counter,
            "SAI_ACL_COUNTER_ATTR_",
        )

    def set_acl_counter_attribute(self, acl_counter):
        status = sai_thrift_set_acl_counter_attribute(
            self.client, acl_counter, bytes=0
        )
        self._assert_status_success(status)

    def remove_acl_counter(self, acl_counter):
        status = sai_thrift_remove_acl_counter(self.client, acl_counter)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 7: ACL Range CRUD
# ===========================================================================

class TestAclRangeCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / remove for ACL Range.
    get iterates all SAI_ACL_RANGE_ATTR_* attributes from
    sai_attr_defaults.csv and validates each returned value against its
    defined default.
    """

    def runTest(self):
        acl_range = self.create_acl_range()
        self.get_acl_range_attribute(acl_range)
        self.remove_acl_range(acl_range)

    def create_acl_range(self):
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=sai_thrift_u32_range_t(min=1024, max=65535),
        )
        self._assert_status_success(adapter.status)
        return acl_range

    def get_acl_range_attribute(self, acl_range):
        _verify_object_attributes(
            self,
            sai_thrift_get_acl_range_attribute,
            acl_range,
            "SAI_ACL_RANGE_ATTR_",
        )

    def remove_acl_range(self, acl_range):
        status = sai_thrift_remove_acl_range(self.client, acl_range)
        self._assert_status_success(status)
