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

Each test class inherits from ThriftInterface (ptf/sai_base_test.py) which
sets up the Thrift RPC connection via setUp/tearDown.  Each class defines a
runTest method that calls create, get, set (where applicable), and remove
helper methods in sequence.  The only assertion in every helper is that the
API returns SAI_STATUS_SUCCESS.

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

import inspect
import sys

from sai_base_test import ThriftInterface

# All SAI API functions, type helpers, and attribute constants are imported
# directly from the generated sai_thrift package (no embedded stubs).
# The package is produced by the saithriftv2 build and placed under
# test/saithriftv2/build/lib/sai_thrift.  If it is not installed this import
# will raise ImportError – build the package first (see module docstring).
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter


# ---------------------------------------------------------------------------
# Helpers to introspect SAI ACL APIs and attributes at test time
# ---------------------------------------------------------------------------

def _get_acl_api_functions():
    """
    Return a sorted list of (name, callable) tuples for every ACL-related
    function exported by sai_thrift.sai_adapter.

    The naming convention used by gensairpc.pl is:
        sai_thrift_create_acl_*
        sai_thrift_remove_acl_*
        sai_thrift_set_acl_*_attribute
        sai_thrift_get_acl_*_attribute
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

    Covers:
      SAI_ACL_TABLE_ATTR_*
      SAI_ACL_ENTRY_ATTR_*
      SAI_ACL_COUNTER_ATTR_*
      SAI_ACL_RANGE_ATTR_*
      SAI_ACL_TABLE_GROUP_ATTR_*
      SAI_ACL_TABLE_GROUP_MEMBER_ATTR_*
      SAI_ACL_TABLE_CHAIN_GROUP_ATTR_*
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
    runTest calls each operation in sequence using a single object.
    Only SAI_STATUS_SUCCESS is verified in each step.
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
        sai_thrift_get_acl_table_group_attribute(
            self.client, acl_table_group, acl_stage=True
        )
        self._assert_status_success(adapter.status)

    def remove_acl_table_group(self, acl_table_group):
        status = sai_thrift_remove_acl_table_group(self.client, acl_table_group)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 3: ACL Table CRUD
# ===========================================================================

class TestAclTableCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / remove for ACL Table.
    runTest calls each operation in sequence using a single object.
    Only SAI_STATUS_SUCCESS is verified in each step.
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
        sai_thrift_get_acl_table_attribute(
            self.client, acl_table, acl_stage=True
        )
        self._assert_status_success(adapter.status)

    def remove_acl_table(self, acl_table):
        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 4: ACL Table Group Member CRUD
# ===========================================================================

class TestAclTableGroupMemberCrud(_SaiAclAssertMixin, ThriftInterface):
    """
    Validates create / get / set / remove for ACL Table Group Member.
    runTest creates the prerequisite ACL table group and table, then calls
    each member operation in sequence using a single object.
    Only SAI_STATUS_SUCCESS is verified in each step.
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
        sai_thrift_get_acl_table_group_member_attribute(
            self.client, member, priority=True
        )
        self._assert_status_success(adapter.status)

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
    runTest creates the prerequisite ACL table, then calls each entry operation
    in sequence using a single object.
    Only SAI_STATUS_SUCCESS is verified in each step.
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
            priority=10,
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
        sai_thrift_get_acl_entry_attribute(
            self.client, acl_entry, priority=True
        )
        self._assert_status_success(adapter.status)

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
    runTest creates the prerequisite ACL table, then calls each counter
    operation in sequence using a single object.
    Only SAI_STATUS_SUCCESS is verified in each step.
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
            self.client, table_id=acl_table, enable_packet_count=True
        )
        self._assert_status_success(adapter.status)
        return acl_counter

    def get_acl_counter_attribute(self, acl_counter):
        sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, packets=True
        )
        self._assert_status_success(adapter.status)

    def set_acl_counter_attribute(self, acl_counter):
        status = sai_thrift_set_acl_counter_attribute(
            self.client, acl_counter, packets=0
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
    runTest calls each operation in sequence using a single object.
    Only SAI_STATUS_SUCCESS is verified in each step.
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
        sai_thrift_get_acl_range_attribute(
            self.client, acl_range, type=True
        )
        self._assert_status_success(adapter.status)

    def remove_acl_range(self, acl_range):
        status = sai_thrift_remove_acl_range(self.client, acl_range)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 8: Full ACL pipeline integration
# ===========================================================================

class TestAclPipelineIntegration(_SaiAclAssertMixin, ThriftInterface):
    """
    Exercises the complete ACL pipeline in a single runTest:

        ACL Table Group
            └── ACL Table Group Member
                    └── ACL Table
                            ├── ACL Entry
                            └── ACL Counter (attached to the entry)

    Only SAI_STATUS_SUCCESS is verified for each API call.
    """

    def runTest(self):
        bp_list = sai_thrift_s32_list_t(
            count=2,
            int32list=[SAI_ACL_BIND_POINT_TYPE_PORT, SAI_ACL_BIND_POINT_TYPE_LAG],
        )

        acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            acl_bind_point_type_list=bp_list,
            type=SAI_ACL_TABLE_GROUP_TYPE_PARALLEL,
        )
        self._assert_status_success(adapter.status, "create group")

        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            acl_bind_point_type_list=bp_list,
            field_src_ip=True,
        )
        self._assert_status_success(adapter.status, "create table")

        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=acl_table_group,
            acl_table_id=acl_table,
            priority=10,
        )
        self._assert_status_success(adapter.status, "create member")

        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=acl_table,
            priority=10,
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
        self._assert_status_success(adapter.status, "create entry")

        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=acl_table, enable_packet_count=True
        )
        self._assert_status_success(adapter.status, "create counter")

        self._assert_status_success(
            sai_thrift_set_acl_entry_attribute(
                self.client,
                acl_entry,
                action_counter=sai_thrift_acl_action_data_t(
                    enable=True,
                    parameter=sai_thrift_acl_action_parameter_t(oid=acl_counter),
                ),
            ),
            "set entry (attach counter)",
        )

        sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, packets=True
        )
        self._assert_status_success(adapter.status, "get counter")

        self._assert_status_success(
            sai_thrift_set_acl_entry_attribute(
                self.client,
                acl_entry,
                action_counter=sai_thrift_acl_action_data_t(
                    enable=False,
                    parameter=sai_thrift_acl_action_parameter_t(oid=0),
                ),
            ),
            "set entry (detach counter)",
        )

        self._assert_status_success(
            sai_thrift_remove_acl_counter(self.client, acl_counter),
            "remove counter",
        )
        self._assert_status_success(
            sai_thrift_remove_acl_entry(self.client, acl_entry),
            "remove entry",
        )
        self._assert_status_success(
            sai_thrift_remove_acl_table_group_member(self.client, member),
            "remove member",
        )
        self._assert_status_success(
            sai_thrift_remove_acl_table(self.client, acl_table),
            "remove table",
        )
        self._assert_status_success(
            sai_thrift_remove_acl_table_group(self.client, acl_table_group),
            "remove group",
        )
