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

Each test class inherits from ThriftInterface (sai_base_test.py) which
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
    ptf --test-dir ptf saiacl_unittests
or:
    python3 -m pytest ptf/saiacl_unittests.py -v
"""

from sai_base_test import ThriftInterface
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter
import sai_thrift.sai_headers as sai_headers

from sai_utils import (
    get_mandatory_on_create_attrs,
    get_mandatory_attrs_from_csv,
    get_sai_api_functions,
    get_sai_attribute_constants,
    verify_object_attributes,
    load_attr_defaults,
)


# Pre-load attribute defaults once at import time.
_ATTR_DEFAULTS = load_attr_defaults()


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
        discovered = {name for name, _ in get_sai_api_functions("_acl_")}
        for func_name in self.EXPECTED_ACL_FUNCTIONS:
            self.assertIn(
                func_name,
                discovered,
                "ACL API function '{}' not found in sai_thrift.sai_adapter. "
                "Discovered ACL functions: {}".format(func_name, sorted(discovered)),
            )

    def verify_acl_attribute_constants(self):
        """At least one attribute constant must exist per expected prefix."""
        constants = get_sai_attribute_constants(sai_headers, *self.EXPECTED_ATTR_PREFIXES)
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
        # Mandatory attrs from CSV: SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE
        # Default value: SAI_ACL_STAGE_INGRESS
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_ACL_TABLE_GROUP_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_ACL_TABLE_GROUP_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, **kwargs
        )
        self._assert_status_success(adapter.status)
        return acl_table_group

    def get_acl_table_group_attribute(self, acl_table_group):
        verify_object_attributes(
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
        # Mandatory attrs from CSV: SAI_ACL_TABLE_ATTR_ACL_STAGE
        # Default value: SAI_ACL_STAGE_INGRESS
        # At least one match field is also required by the SAI spec;
        # field_src_ip is added as the minimal match field.
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_ACL_TABLE_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_ACL_TABLE_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["field_src_ip"] = True
        acl_table = sai_thrift_create_acl_table(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return acl_table

    def get_acl_table_attribute(self, acl_table):
        verify_object_attributes(
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
        # Create prerequisites using CSV mandatory attributes.
        grp_kwargs = {
            attr[len("SAI_ACL_TABLE_GROUP_ATTR_"):].lower():
                getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv(
                "SAI_ACL_TABLE_GROUP_ATTR_", _ATTR_DEFAULTS
            )
            for _, default, _ in [_ATTR_DEFAULTS[attr]]
            if default
        }
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, **grp_kwargs
        )

        tbl_kwargs = {
            attr[len("SAI_ACL_TABLE_ATTR_"):].lower():
                getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv(
                "SAI_ACL_TABLE_ATTR_", _ATTR_DEFAULTS
            )
            for _, default, _ in [_ATTR_DEFAULTS[attr]]
            if default
        }
        tbl_kwargs["field_src_ip"] = True
        acl_table = sai_thrift_create_acl_table(self.client, **tbl_kwargs)

        member = self.create_acl_table_group_member(acl_table_group, acl_table)
        self.get_acl_table_group_member_attribute(member)
        self.set_acl_table_group_member_attribute(member)
        self.remove_acl_table_group_member(member)

        sai_thrift_remove_acl_table(self.client, acl_table)
        sai_thrift_remove_acl_table_group(self.client, acl_table_group)

    def create_acl_table_group_member(self, acl_table_group, acl_table):
        # Mandatory attrs from CSV:
        #   SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_GROUP_ID (OID, no default)
        #   SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_ID       (OID, no default)
        #   SAI_ACL_TABLE_GROUP_MEMBER_ATTR_PRIORITY           (uint32, no default)
        # OID attrs have no CSV default and are supplied by the caller;
        # priority has no CSV default so a value of 10 is used.
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_ACL_TABLE_GROUP_MEMBER_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # Supply runtime OID values for attrs with no CSV default.
        kwargs["acl_table_group_id"] = acl_table_group
        kwargs["acl_table_id"] = acl_table
        kwargs.setdefault("priority", 10)
        member = sai_thrift_create_acl_table_group_member(
            self.client, **kwargs
        )
        self._assert_status_success(adapter.status)
        return member

    def get_acl_table_group_member_attribute(self, member):
        verify_object_attributes(
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
        tbl_kwargs = {
            attr[len("SAI_ACL_TABLE_ATTR_"):].lower():
                getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv(
                "SAI_ACL_TABLE_ATTR_", _ATTR_DEFAULTS
            )
            for _, default, _ in [_ATTR_DEFAULTS[attr]]
            if default
        }
        tbl_kwargs["field_src_ip"] = True
        acl_table = sai_thrift_create_acl_table(self.client, **tbl_kwargs)

        acl_entry = self.create_acl_entry(acl_table)
        self.get_acl_entry_attribute(acl_entry)
        self.set_acl_entry_attribute(acl_entry)
        self.remove_acl_entry(acl_entry)

        sai_thrift_remove_acl_table(self.client, acl_table)

    def create_acl_entry(self, acl_table):
        # Mandatory attrs from CSV:
        #   SAI_ACL_ENTRY_ATTR_TABLE_ID  (OID, no default)
        # At least one match field is required by the SAI spec;
        # field_src_ip with a DROP action is added as the minimal entry.
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_ACL_ENTRY_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_ACL_ENTRY_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # Supply OID for table_id (no CSV default).
        kwargs["table_id"] = acl_table
        # Add minimal match field and action.
        kwargs["field_src_ip"] = sai_thrift_acl_field_data_t(
            enable=True,
            data=sai_thrift_acl_field_data_data_t(ip4="10.0.0.1"),
            mask=sai_thrift_acl_field_data_mask_t(ip4="255.255.255.255"),
        )
        kwargs["action_packet_action"] = sai_thrift_acl_action_data_t(
            enable=True,
            parameter=sai_thrift_acl_action_parameter_t(
                s32=SAI_PACKET_ACTION_DROP
            ),
        )
        acl_entry = sai_thrift_create_acl_entry(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return acl_entry

    def get_acl_entry_attribute(self, acl_entry):
        verify_object_attributes(
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
        tbl_kwargs = {
            attr[len("SAI_ACL_TABLE_ATTR_"):].lower():
                getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv(
                "SAI_ACL_TABLE_ATTR_", _ATTR_DEFAULTS
            )
            for _, default, _ in [_ATTR_DEFAULTS[attr]]
            if default
        }
        tbl_kwargs["field_src_ip"] = True
        acl_table = sai_thrift_create_acl_table(self.client, **tbl_kwargs)

        acl_counter = self.create_acl_counter(acl_table)
        self.get_acl_counter_attribute(acl_counter)
        self.set_acl_counter_attribute(acl_counter)
        self.remove_acl_counter(acl_counter)

        sai_thrift_remove_acl_table(self.client, acl_table)

    def create_acl_counter(self, acl_table):
        # Mandatory attrs from CSV:
        #   SAI_ACL_COUNTER_ATTR_TABLE_ID  (OID, no default)
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_ACL_COUNTER_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_ACL_COUNTER_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["table_id"] = acl_table
        acl_counter = sai_thrift_create_acl_counter(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return acl_counter

    def get_acl_counter_attribute(self, acl_counter):
        verify_object_attributes(
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
        # Mandatory attrs from CSV:
        #   SAI_ACL_RANGE_ATTR_TYPE   (enum, default SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE)
        #   SAI_ACL_RANGE_ATTR_LIMIT  (sai_u32_range_t, no default)
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_ACL_RANGE_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_ACL_RANGE_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # Supply limit (no CSV default).
        kwargs["limit"] = sai_thrift_u32_range_t(min=1024, max=65535)
        acl_range = sai_thrift_create_acl_range(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return acl_range

    def get_acl_range_attribute(self, acl_range):
        verify_object_attributes(
            self,
            sai_thrift_get_acl_range_attribute,
            acl_range,
            "SAI_ACL_RANGE_ATTR_",
        )

    def remove_acl_range(self, acl_range):
        status = sai_thrift_remove_acl_range(self.client, acl_range)
        self._assert_status_success(status)
