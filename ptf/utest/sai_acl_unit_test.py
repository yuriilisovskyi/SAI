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

One test per ACL API.  Within each test class the SAI object is created
once by the create test and reused by the get / set / remove tests.
The only assertion in every test is that the API returns SAI_STATUS_SUCCESS.

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
     By default the tests connect to localhost:9092.
     Override with the THRIFT_SERVER environment variable:
       export THRIFT_SERVER=<host>

Run with:
    python3 -m pytest ptf/utest/sai_acl_unit_test.py -v
or:
    python3 -m unittest discover -s ptf/utest -p sai_acl_unit_test.py
"""

import inspect
import os
import sys
import unittest

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# All SAI API functions, type helpers, and attribute constants are imported
# directly from the generated sai_thrift package (no embedded stubs).
# The package is produced by the saithriftv2 build and placed under
# test/saithriftv2/build/lib/sai_thrift.  If it is not installed this import
# will raise ImportError – build the package first (see module docstring).
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
from sai_thrift import sai_rpc
import sai_thrift.sai_adapter as adapter

THRIFT_PORT = 9092


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
# Base class shared by all SAI ACL test classes that call the RPC server
# ---------------------------------------------------------------------------

class SaiAclTestBase(unittest.TestCase):
    """
    Opens a single Thrift connection to the SAI RPC server for the entire
    test class (setUpClass / tearDownClass) so that all tests within a class
    share the same connection and the same pre-created SAI objects.

    The server address is taken from the THRIFT_SERVER environment variable,
    defaulting to 'localhost'.
    """

    client = None
    transport = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        server = os.environ.get('THRIFT_SERVER', 'localhost')
        transport = TSocket.TSocket(server, THRIFT_PORT)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        cls.client = sai_rpc.Client(protocol)
        cls.transport = transport
        cls.transport.open()

    @classmethod
    def tearDownClass(cls):
        cls.transport.close()
        super().tearDownClass()

    def _assert_status_success(self, status, msg=""):
        self.assertEqual(
            status,
            SAI_STATUS_SUCCESS,
            msg or "Expected SAI_STATUS_SUCCESS (0), got {}".format(status),
        )


# ===========================================================================
# Test Class 1: Discover ACL APIs and attributes from sai_thrift
# (introspects Python modules only; no SAI server connection required)
# ===========================================================================

class TestAclApiDiscovery(unittest.TestCase):
    """
    Verifies that sai_thrift exposes the expected set of SAI ACL API functions
    and attribute constants.

    All symbols are discovered at runtime from the installed sai_thrift package
    (test/saithriftv2/build/lib/sai_thrift) – no hard-coded fallback values.
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

    def test_acl_api_functions_discoverable(self):
        """
        All expected ACL CRUD functions must be present in
        sai_thrift.sai_adapter (sourced from test/saithriftv2/build/lib).
        """
        discovered = {name for name, _ in _get_acl_api_functions()}
        for func_name in self.EXPECTED_ACL_FUNCTIONS:
            self.assertIn(
                func_name,
                discovered,
                "ACL API function '{}' not found in sai_thrift.sai_adapter. "
                "Discovered ACL functions: {}".format(
                    func_name, sorted(discovered)
                ),
            )

    def test_acl_attribute_constants_discoverable(self):
        """
        At least one attribute constant must exist per expected prefix
        (sourced from sai_thrift.sai_headers).
        """
        constants = _get_acl_attribute_constants()
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            matching = [k for k in constants if k.startswith(prefix)]
            self.assertTrue(
                len(matching) > 0,
                "No attribute constants with prefix '{}' found in "
                "sai_thrift.sai_headers. "
                "Available ACL constants: {}".format(
                    prefix, sorted(constants.keys())
                ),
            )


# ===========================================================================
# Test Class 2: ACL Table Group CRUD – one test per API
# ===========================================================================

class TestAclTableGroupCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Table Group API.
    The object created by test_01 is reused by test_02 and removed by test_03.
    Only SAI_STATUS_SUCCESS is verified in each test.
    """

    acl_table_group = None

    def test_01_create_acl_table_group(self):
        TestAclTableGroupCrud.acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
        )
        self._assert_status_success(adapter.status)

    def test_02_get_acl_table_group_attribute(self):
        sai_thrift_get_acl_table_group_attribute(
            self.client, self.__class__.acl_table_group, acl_stage=True
        )
        self._assert_status_success(adapter.status)

    def test_03_remove_acl_table_group(self):
        status = sai_thrift_remove_acl_table_group(
            self.client, self.__class__.acl_table_group
        )
        self._assert_status_success(status)


# ===========================================================================
# Test Class 3: ACL Table CRUD – one test per API
# ===========================================================================

class TestAclTableCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Table API.
    The object created by test_01 is reused by test_02 and removed by test_03.
    Only SAI_STATUS_SUCCESS is verified in each test.
    """

    acl_table = None

    def test_01_create_acl_table(self):
        TestAclTableCrud.acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            field_src_ip=True,
        )
        self._assert_status_success(adapter.status)

    def test_02_get_acl_table_attribute(self):
        sai_thrift_get_acl_table_attribute(
            self.client, self.__class__.acl_table, acl_stage=True
        )
        self._assert_status_success(adapter.status)

    def test_03_remove_acl_table(self):
        status = sai_thrift_remove_acl_table(
            self.client, self.__class__.acl_table
        )
        self._assert_status_success(status)


# ===========================================================================
# Test Class 4: ACL Table Group Member CRUD – one test per API
# ===========================================================================

class TestAclTableGroupMemberCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Table Group Member API.
    Prerequisites (acl_table_group, acl_table) are created once in setUpClass.
    The member object created by test_01 is reused by test_02/03 and
    removed by test_04.
    Only SAI_STATUS_SUCCESS is verified in each test.
    """

    acl_table_group = None
    acl_table = None
    member = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acl_table_group = sai_thrift_create_acl_table_group(
            cls.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        cls.acl_table = sai_thrift_create_acl_table(
            cls.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

    @classmethod
    def tearDownClass(cls):
        if cls.member is not None:
            sai_thrift_remove_acl_table_group_member(cls.client, cls.member)
        sai_thrift_remove_acl_table(cls.client, cls.acl_table)
        sai_thrift_remove_acl_table_group(cls.client, cls.acl_table_group)
        super().tearDownClass()

    def test_01_create_acl_table_group_member(self):
        TestAclTableGroupMemberCrud.member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.__class__.acl_table_group,
            acl_table_id=self.__class__.acl_table,
            priority=10,
        )
        self._assert_status_success(adapter.status)

    def test_02_get_acl_table_group_member_attribute(self):
        sai_thrift_get_acl_table_group_member_attribute(
            self.client, self.__class__.member, priority=True
        )
        self._assert_status_success(adapter.status)

    def test_03_set_acl_table_group_member_attribute(self):
        status = sai_thrift_set_acl_table_group_member_attribute(
            self.client, self.__class__.member
        )
        self._assert_status_success(status)

    def test_04_remove_acl_table_group_member(self):
        status = sai_thrift_remove_acl_table_group_member(
            self.client, self.__class__.member
        )
        self._assert_status_success(status)
        TestAclTableGroupMemberCrud.member = None


# ===========================================================================
# Test Class 5: ACL Entry CRUD – one test per API
# ===========================================================================

class TestAclEntryCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Entry API.
    The ACL table prerequisite is created once in setUpClass.
    The entry object created by test_01 is reused by test_02/03 and
    removed by test_04.
    Only SAI_STATUS_SUCCESS is verified in each test.
    """

    acl_table = None
    acl_entry = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acl_table = sai_thrift_create_acl_table(
            cls.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

    @classmethod
    def tearDownClass(cls):
        if cls.acl_entry is not None:
            sai_thrift_remove_acl_entry(cls.client, cls.acl_entry)
        sai_thrift_remove_acl_table(cls.client, cls.acl_table)
        super().tearDownClass()

    def test_01_create_acl_entry(self):
        TestAclEntryCrud.acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.__class__.acl_table,
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

    def test_02_get_acl_entry_attribute(self):
        sai_thrift_get_acl_entry_attribute(
            self.client, self.__class__.acl_entry, priority=True
        )
        self._assert_status_success(adapter.status)

    def test_03_set_acl_entry_attribute(self):
        status = sai_thrift_set_acl_entry_attribute(
            self.client, self.__class__.acl_entry, priority=20
        )
        self._assert_status_success(status)

    def test_04_remove_acl_entry(self):
        status = sai_thrift_remove_acl_entry(
            self.client, self.__class__.acl_entry
        )
        self._assert_status_success(status)
        TestAclEntryCrud.acl_entry = None


# ===========================================================================
# Test Class 6: ACL Counter CRUD – one test per API
# ===========================================================================

class TestAclCounterCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Counter API.
    The ACL table prerequisite is created once in setUpClass.
    The counter object created by test_01 is reused by test_02/03 and
    removed by test_04.
    Only SAI_STATUS_SUCCESS is verified in each test.
    """

    acl_table = None
    acl_counter = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acl_table = sai_thrift_create_acl_table(
            cls.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

    @classmethod
    def tearDownClass(cls):
        if cls.acl_counter is not None:
            sai_thrift_remove_acl_counter(cls.client, cls.acl_counter)
        sai_thrift_remove_acl_table(cls.client, cls.acl_table)
        super().tearDownClass()

    def test_01_create_acl_counter(self):
        TestAclCounterCrud.acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.__class__.acl_table, enable_packet_count=True
        )
        self._assert_status_success(adapter.status)

    def test_02_get_acl_counter_attribute(self):
        sai_thrift_get_acl_counter_attribute(
            self.client, self.__class__.acl_counter, packets=True
        )
        self._assert_status_success(adapter.status)

    def test_03_set_acl_counter_attribute(self):
        status = sai_thrift_set_acl_counter_attribute(
            self.client, self.__class__.acl_counter, packets=0
        )
        self._assert_status_success(status)

    def test_04_remove_acl_counter(self):
        status = sai_thrift_remove_acl_counter(
            self.client, self.__class__.acl_counter
        )
        self._assert_status_success(status)
        TestAclCounterCrud.acl_counter = None


# ===========================================================================
# Test Class 7: ACL Range CRUD – one test per API
# ===========================================================================

class TestAclRangeCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Range API.
    The object created by test_01 is reused by test_02 and removed by test_03.
    Only SAI_STATUS_SUCCESS is verified in each test.
    """

    acl_range = None

    def test_01_create_acl_range(self):
        TestAclRangeCrud.acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=sai_thrift_u32_range_t(min=1024, max=65535),
        )
        self._assert_status_success(adapter.status)

    def test_02_get_acl_range_attribute(self):
        sai_thrift_get_acl_range_attribute(
            self.client, self.__class__.acl_range, type=True
        )
        self._assert_status_success(adapter.status)

    def test_03_remove_acl_range(self):
        status = sai_thrift_remove_acl_range(
            self.client, self.__class__.acl_range
        )
        self._assert_status_success(status)


# ===========================================================================
# Test Class 8: Full ACL pipeline integration
# ===========================================================================

class TestAclPipelineIntegration(SaiAclTestBase):
    """
    Exercises the complete ACL pipeline in a single test:

        ACL Table Group
            └── ACL Table Group Member
                    └── ACL Table
                            ├── ACL Entry
                            └── ACL Counter (attached to the entry)

    Only SAI_STATUS_SUCCESS is verified for each API call.
    """

    def test_acl_pipeline(self):
        """
        Build and teardown the full ACL pipeline:
          create group → create table → create member → create entry →
          create counter → set entry (attach counter) →
          get counter → set entry (detach counter) →
          remove counter → remove entry → remove member →
          remove table → remove group.
        """
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


if __name__ == "__main__":
    unittest.main()
