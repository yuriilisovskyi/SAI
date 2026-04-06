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

One test is provided per meaningful ACL API call:

  ACL Table Group        create / get / remove
  ACL Table Group Member create / get / set / remove
  ACL Table              create / get / remove
  ACL Entry              create / get / set / remove
  ACL Counter            create / get / set / remove
  ACL Range              create / get / remove

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
# Base class shared by all ACL unit-test classes
# ---------------------------------------------------------------------------

class SaiAclTestBase(unittest.TestCase):
    """
    Base class for SAI ACL unit tests.

    Opens a Thrift connection to the SAI RPC server in setUp and closes it
    in tearDown.  The server address is taken from the THRIFT_SERVER
    environment variable, defaulting to 'localhost'.

    Attributes:
        client    – sai_rpc.Client connected to the SAI RPC server
        transport – Thrift transport (closed in tearDown)
    """

    def setUp(self):
        super().setUp()
        server = os.environ.get('THRIFT_SERVER', 'localhost')
        transport = TSocket.TSocket(server, THRIFT_PORT)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        self.client = sai_rpc.Client(protocol)
        self.transport = transport
        self.transport.open()

    def tearDown(self):
        self.transport.close()
        super().tearDown()

    def _assert_status_success(self, status, msg=""):
        self.assertEqual(
            status,
            SAI_STATUS_SUCCESS,
            msg or "Expected SAI_STATUS_SUCCESS (0), got {}".format(status),
        )

    def _assert_valid_oid(self, oid, msg=""):
        self.assertNotEqual(
            oid, 0,
            msg or "Expected a non-zero SAI object OID, got 0",
        )


# ===========================================================================
# Test Class 1: Discover ACL APIs and attributes from sai_thrift
# ===========================================================================

class TestAclApiDiscovery(SaiAclTestBase):
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
    One test per sai_thrift ACL Table Group API:
      sai_thrift_create_acl_table_group
      sai_thrift_get_acl_table_group_attribute
      sai_thrift_remove_acl_table_group

    Note: sai_thrift_set_acl_table_group_attribute is not tested here because
    all ACL Table Group attributes are CREATE_ONLY in the SAI spec; the
    generated adapter function returns SAI_STATUS_NOT_SUPPORTED by design.
    """

    def test_create_acl_table_group(self):
        """
        sai_thrift_create_acl_table_group with default values.
        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
        )
        self._assert_valid_oid(acl_table_group)
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_table_group(self.client, acl_table_group)

    def test_get_acl_table_group_attribute(self):
        """
        sai_thrift_get_acl_table_group_attribute with default values.
        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        attr = sai_thrift_get_acl_table_group_attribute(
            self.client, acl_table_group, acl_stage=True
        )
        self._assert_status_success(adapter.status)
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_table_group(self.client, acl_table_group)

    def test_remove_acl_table_group(self):
        """
        sai_thrift_remove_acl_table_group with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        status = sai_thrift_remove_acl_table_group(self.client, acl_table_group)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 3: ACL Table CRUD – one test per API
# ===========================================================================

class TestAclTableCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Table API:
      sai_thrift_create_acl_table
      sai_thrift_get_acl_table_attribute
      sai_thrift_remove_acl_table

    Note: sai_thrift_set_acl_table_attribute is not tested here because
    all ACL Table attributes are CREATE_ONLY in the SAI spec; the generated
    adapter function returns SAI_STATUS_NOT_SUPPORTED by design.
    """

    def test_create_acl_table(self):
        """
        sai_thrift_create_acl_table with default values.
        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            field_src_ip=True,
        )
        self._assert_valid_oid(acl_table)
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_table(self.client, acl_table)

    def test_get_acl_table_attribute(self):
        """
        sai_thrift_get_acl_table_attribute with default values.
        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )
        attr = sai_thrift_get_acl_table_attribute(
            self.client, acl_table, acl_stage=True
        )
        self._assert_status_success(adapter.status)
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_table(self.client, acl_table)

    def test_remove_acl_table(self):
        """
        sai_thrift_remove_acl_table with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )
        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 4: ACL Table Group Member CRUD – one test per API
# ===========================================================================

class TestAclTableGroupMemberCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Table Group Member API:
      sai_thrift_create_acl_table_group_member
      sai_thrift_get_acl_table_group_member_attribute
      sai_thrift_set_acl_table_group_member_attribute
      sai_thrift_remove_acl_table_group_member

    Prerequisites created in setUp:
      - ACL Table Group (acl_stage=SAI_ACL_STAGE_INGRESS)
      - ACL Table       (acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True)
    """

    def setUp(self):
        super().setUp()
        self.acl_table_group = sai_thrift_create_acl_table_group(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        self.acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

    def tearDown(self):
        sai_thrift_remove_acl_table(self.client, self.acl_table)
        sai_thrift_remove_acl_table_group(self.client, self.acl_table_group)
        super().tearDown()

    def test_create_acl_table_group_member(self):
        """
        sai_thrift_create_acl_table_group_member with default values.
        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=10,
        )
        self._assert_valid_oid(member)
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_table_group_member(self.client, member)

    def test_get_acl_table_group_member_attribute(self):
        """
        sai_thrift_get_acl_table_group_member_attribute with default values.
        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=10,
        )
        attr = sai_thrift_get_acl_table_group_member_attribute(
            self.client, member, priority=True
        )
        self._assert_status_success(adapter.status)
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_table_group_member(self.client, member)

    def test_set_acl_table_group_member_attribute(self):
        """
        sai_thrift_set_acl_table_group_member_attribute with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=10,
        )
        status = sai_thrift_set_acl_table_group_member_attribute(
            self.client, member
        )
        self._assert_status_success(status)
        sai_thrift_remove_acl_table_group_member(self.client, member)

    def test_remove_acl_table_group_member(self):
        """
        sai_thrift_remove_acl_table_group_member with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=10,
        )
        status = sai_thrift_remove_acl_table_group_member(self.client, member)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 5: ACL Entry CRUD – one test per API
# ===========================================================================

class TestAclEntryCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Entry API:
      sai_thrift_create_acl_entry
      sai_thrift_get_acl_entry_attribute
      sai_thrift_set_acl_entry_attribute
      sai_thrift_remove_acl_entry

    Prerequisite created in setUp:
      - ACL Table (acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True)
    """

    def setUp(self):
        super().setUp()
        self.acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

    def tearDown(self):
        sai_thrift_remove_acl_table(self.client, self.acl_table)
        super().tearDown()

    def _make_acl_entry(self):
        return sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
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

    def test_create_acl_entry(self):
        """
        sai_thrift_create_acl_entry with default values.
        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_entry = self._make_acl_entry()
        self._assert_valid_oid(acl_entry)
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_get_acl_entry_attribute(self):
        """
        sai_thrift_get_acl_entry_attribute with default values.
        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_entry = self._make_acl_entry()
        attr = sai_thrift_get_acl_entry_attribute(
            self.client, acl_entry, priority=True
        )
        self._assert_status_success(adapter.status)
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_set_acl_entry_attribute(self):
        """
        sai_thrift_set_acl_entry_attribute with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        acl_entry = self._make_acl_entry()
        status = sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, priority=20
        )
        self._assert_status_success(status)
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_remove_acl_entry(self):
        """
        sai_thrift_remove_acl_entry with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        acl_entry = self._make_acl_entry()
        status = sai_thrift_remove_acl_entry(self.client, acl_entry)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 6: ACL Counter CRUD – one test per API
# ===========================================================================

class TestAclCounterCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Counter API:
      sai_thrift_create_acl_counter
      sai_thrift_get_acl_counter_attribute
      sai_thrift_set_acl_counter_attribute
      sai_thrift_remove_acl_counter

    Prerequisite created in setUp:
      - ACL Table (acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True)
    """

    def setUp(self):
        super().setUp()
        self.acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

    def tearDown(self):
        sai_thrift_remove_acl_table(self.client, self.acl_table)
        super().tearDown()

    def test_create_acl_counter(self):
        """
        sai_thrift_create_acl_counter with default values.
        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table
        )
        self._assert_valid_oid(acl_counter)
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_get_acl_counter_attribute(self):
        """
        sai_thrift_get_acl_counter_attribute with default values.
        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table, enable_packet_count=True
        )
        attr = sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, packets=True
        )
        self._assert_status_success(adapter.status)
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_set_acl_counter_attribute(self):
        """
        sai_thrift_set_acl_counter_attribute with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table, enable_packet_count=True
        )
        status = sai_thrift_set_acl_counter_attribute(
            self.client, acl_counter, packets=0
        )
        self._assert_status_success(status)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_remove_acl_counter(self):
        """
        sai_thrift_remove_acl_counter with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table
        )
        status = sai_thrift_remove_acl_counter(self.client, acl_counter)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 7: ACL Range CRUD – one test per API
# ===========================================================================

class TestAclRangeCrud(SaiAclTestBase):
    """
    One test per sai_thrift ACL Range API:
      sai_thrift_create_acl_range
      sai_thrift_get_acl_range_attribute
      sai_thrift_remove_acl_range

    Note: sai_thrift_set_acl_range_attribute is not tested here because
    all ACL Range attributes are CREATE_ONLY in the SAI spec; the generated
    adapter function returns SAI_STATUS_NOT_SUPPORTED by design.
    """

    def test_create_acl_range(self):
        """
        sai_thrift_create_acl_range with default values.
        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=sai_thrift_u32_range_t(min=1024, max=65535),
        )
        self._assert_valid_oid(acl_range)
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_get_acl_range_attribute(self):
        """
        sai_thrift_get_acl_range_attribute with default values.
        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=sai_thrift_u32_range_t(min=1024, max=65535),
        )
        attr = sai_thrift_get_acl_range_attribute(
            self.client, acl_range, type=True
        )
        self._assert_status_success(adapter.status)
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_remove_acl_range(self):
        """
        sai_thrift_remove_acl_range with default values.
        Expected: SAI_STATUS_SUCCESS.
        """
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=sai_thrift_u32_range_t(min=1024, max=65535),
        )
        status = sai_thrift_remove_acl_range(self.client, acl_range)
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

    Verifies that all ACL API calls interoperate and that every call
    returns SAI_STATUS_SUCCESS.
    """

    def test_acl_pipeline(self):
        """
        Build and teardown the full ACL pipeline with default values:
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
        self._assert_valid_oid(acl_table_group, "create group")
        self._assert_status_success(adapter.status)

        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            acl_bind_point_type_list=bp_list,
            field_src_ip=True,
        )
        self._assert_valid_oid(acl_table, "create table")
        self._assert_status_success(adapter.status)

        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=acl_table_group,
            acl_table_id=acl_table,
            priority=10,
        )
        self._assert_valid_oid(member, "create member")
        self._assert_status_success(adapter.status)

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
        self._assert_valid_oid(acl_entry, "create entry")
        self._assert_status_success(adapter.status)

        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=acl_table, enable_packet_count=True
        )
        self._assert_valid_oid(acl_counter, "create counter")
        self._assert_status_success(adapter.status)

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

        attr = sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, packets=True
        )
        self._assert_status_success(adapter.status, "get counter")
        self.assertIsNotNone(attr)

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
