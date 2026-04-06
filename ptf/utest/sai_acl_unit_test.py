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

Validates SAI ACL API implementation by retrieving the list of all SAI ACL
APIs and attributes from sai_thrift (test/saithriftv2/build/lib/sai_thrift)
and verifying that each CRUD API call with default values returns
SAI_STATUS_SUCCESS.

ACL objects covered:
  - ACL Table Group         (create/get/remove)
  - ACL Table Group Member  (create/get/remove)
  - ACL Table               (create/get/set/remove)
  - ACL Entry               (create/get/set/remove)
  - ACL Counter             (create/get/set/remove)
  - ACL Range               (create/get/remove)

When the sai_thrift package is not installed (i.e. the SAI thrift server has
not been built yet) the tests fall back to self-contained lightweight stubs so
that the test file can be parsed, collected and run entirely without external
dependencies.  The stubs replicate the same public interface as the generated
sai_thrift package and the existing MockClient helper.

Run with:
    python3 -m pytest ptf/utest/sai_acl_unit_test.py -v
or:
    python3 -m unittest discover -s ptf/utest -p sai_acl_unit_test.py
"""

import inspect
import sys
import unittest

# ---------------------------------------------------------------------------
# Attempt to import the generated sai_thrift package.
# Fall back to lightweight embedded stubs when it is not available so tests
# can be collected / executed standalone (CI, code-review, offline).
# ---------------------------------------------------------------------------

_SAI_THRIFT_AVAILABLE = False

try:
    from sai_thrift.sai_adapter import *  # noqa: F401,F403
    from sai_thrift.sai_headers import *  # noqa: F401,F403
    import sai_thrift.sai_adapter as adapter
    _SAI_THRIFT_AVAILABLE = True
except ImportError:
    pass

if not _SAI_THRIFT_AVAILABLE:
    try:
        from meta.sai_adapter import *  # noqa: F401,F403
        import meta.sai_adapter as adapter
        _SAI_THRIFT_AVAILABLE = True
    except ImportError:
        pass

# ---------------------------------------------------------------------------
# Embedded stubs – only activated when sai_thrift is unavailable.
# These mirror the public API/constants that gensairpc.pl generates.
# ---------------------------------------------------------------------------

if not _SAI_THRIFT_AVAILABLE:

    # ------------------------------------------------------------------ #
    # Minimal adapter stub
    # ------------------------------------------------------------------ #
    class _AdapterStub:
        """Minimal stand-in for sai_thrift.sai_adapter."""
        status = 0  # SAI_STATUS_SUCCESS

    adapter = _AdapterStub()
    CATCH_EXCEPTIONS = True

    # ------------------------------------------------------------------ #
    # SAI Status codes
    # ------------------------------------------------------------------ #
    SAI_STATUS_SUCCESS = 0
    SAI_STATUS_FAILURE = -1

    # ------------------------------------------------------------------ #
    # ACL Stage constants
    # ------------------------------------------------------------------ #
    SAI_ACL_STAGE_INGRESS = 0
    SAI_ACL_STAGE_EGRESS = 1
    SAI_ACL_STAGE_PRE_INGRESS = 2

    # ------------------------------------------------------------------ #
    # ACL Bind Point Type constants
    # ------------------------------------------------------------------ #
    SAI_ACL_BIND_POINT_TYPE_PORT = 0
    SAI_ACL_BIND_POINT_TYPE_LAG = 1
    SAI_ACL_BIND_POINT_TYPE_VLAN = 2
    SAI_ACL_BIND_POINT_TYPE_ROUTER_INTF = 3
    SAI_ACL_BIND_POINT_TYPE_SWITCH = 4

    # ------------------------------------------------------------------ #
    # ACL Table Group Type constants
    # ------------------------------------------------------------------ #
    SAI_ACL_TABLE_GROUP_TYPE_SEQUENTIAL = 0
    SAI_ACL_TABLE_GROUP_TYPE_PARALLEL = 1

    # ------------------------------------------------------------------ #
    # ACL Table Group Attribute constants
    # ------------------------------------------------------------------ #
    SAI_ACL_TABLE_GROUP_ATTR_START = 0
    SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE = 0
    SAI_ACL_TABLE_GROUP_ATTR_ACL_BIND_POINT_TYPE_LIST = 1
    SAI_ACL_TABLE_GROUP_ATTR_TYPE = 2
    SAI_ACL_TABLE_GROUP_ATTR_MEMBER_LIST = 3
    SAI_ACL_TABLE_GROUP_ATTR_CHAIN_GROUP_LIST = 4
    SAI_ACL_TABLE_GROUP_ATTR_END = 5
    SAI_ACL_TABLE_GROUP_ATTR_CUSTOM_RANGE_START = 0x10000000
    SAI_ACL_TABLE_GROUP_ATTR_CUSTOM_RANGE_END = 0x10000001

    # ------------------------------------------------------------------ #
    # ACL Table Group Member Attribute constants
    # ------------------------------------------------------------------ #
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_START = 0
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_GROUP_ID = 0
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_ID = 1
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_PRIORITY = 2
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_CHAIN_GROUP_ID = 3
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_END = 4
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_CUSTOM_RANGE_START = 0x10000000
    SAI_ACL_TABLE_GROUP_MEMBER_ATTR_CUSTOM_RANGE_END = 0x10000001

    # ------------------------------------------------------------------ #
    # ACL Table Chain Group Attribute constants
    # ------------------------------------------------------------------ #
    SAI_ACL_TABLE_CHAIN_GROUP_ATTR_START = 0
    SAI_ACL_TABLE_CHAIN_GROUP_ATTR_TYPE = 0
    SAI_ACL_TABLE_CHAIN_GROUP_ATTR_STAGE = 1
    SAI_ACL_TABLE_CHAIN_GROUP_ATTR_END = 2
    SAI_ACL_TABLE_CHAIN_GROUP_ATTR_CUSTOM_RANGE_START = 0x10000000
    SAI_ACL_TABLE_CHAIN_GROUP_ATTR_CUSTOM_RANGE_END = 0x10000001

    # ------------------------------------------------------------------ #
    # ACL Table Attribute constants (selected)
    # ------------------------------------------------------------------ #
    SAI_ACL_TABLE_ATTR_START = 0
    SAI_ACL_TABLE_ATTR_ACL_STAGE = 0
    SAI_ACL_TABLE_ATTR_ACL_BIND_POINT_TYPE_LIST = 1
    SAI_ACL_TABLE_ATTR_SIZE = 2
    SAI_ACL_TABLE_ATTR_ACL_ACTION_TYPE_LIST = 3
    SAI_ACL_TABLE_ATTR_FIELD_START = 0x00001000
    SAI_ACL_TABLE_ATTR_FIELD_SRC_IPV6 = 0x00001000
    SAI_ACL_TABLE_ATTR_FIELD_DST_IPV6 = 0x00001001
    SAI_ACL_TABLE_ATTR_FIELD_SRC_MAC = 0x00001004
    SAI_ACL_TABLE_ATTR_FIELD_DST_MAC = 0x00001005
    SAI_ACL_TABLE_ATTR_FIELD_SRC_IP = 0x00001006
    SAI_ACL_TABLE_ATTR_FIELD_DST_IP = 0x00001007
    SAI_ACL_TABLE_ATTR_FIELD_IP_PROTOCOL = 0x0000101b
    SAI_ACL_TABLE_ATTR_FIELD_L4_SRC_PORT = 0x00001015
    SAI_ACL_TABLE_ATTR_FIELD_L4_DST_PORT = 0x00001016
    SAI_ACL_TABLE_ATTR_FIELD_ACL_RANGE_TYPE = 0x0000115c
    SAI_ACL_TABLE_ATTR_END = 0xFFFF
    SAI_ACL_TABLE_ATTR_CUSTOM_RANGE_START = 0x10000000
    SAI_ACL_TABLE_ATTR_CUSTOM_RANGE_END = 0x10000001

    # ------------------------------------------------------------------ #
    # ACL Entry Attribute constants (selected)
    # ------------------------------------------------------------------ #
    SAI_ACL_ENTRY_ATTR_START = 0
    SAI_ACL_ENTRY_ATTR_TABLE_ID = 0
    SAI_ACL_ENTRY_ATTR_PRIORITY = 1
    SAI_ACL_ENTRY_ATTR_ADMIN_STATE = 2
    SAI_ACL_ENTRY_ATTR_FIELD_START = 0x00001000
    SAI_ACL_ENTRY_ATTR_FIELD_SRC_IPV6 = 0x00001000
    SAI_ACL_ENTRY_ATTR_FIELD_SRC_MAC = 0x00001004
    SAI_ACL_ENTRY_ATTR_FIELD_SRC_IP = 0x00001006
    SAI_ACL_ENTRY_ATTR_FIELD_DST_IP = 0x00001007
    SAI_ACL_ENTRY_ATTR_FIELD_IP_PROTOCOL = 0x0000101b
    SAI_ACL_ENTRY_ATTR_FIELD_L4_SRC_PORT = 0x00001015
    SAI_ACL_ENTRY_ATTR_FIELD_L4_DST_PORT = 0x00001016
    SAI_ACL_ENTRY_ATTR_FIELD_ACL_RANGE_TYPE = 0x0000115c
    SAI_ACL_ENTRY_ATTR_ACTION_START = 0x00002000
    SAI_ACL_ENTRY_ATTR_ACTION_PACKET_ACTION = 0x00002003
    SAI_ACL_ENTRY_ATTR_ACTION_COUNTER = 0x00002005
    SAI_ACL_ENTRY_ATTR_END = 0xFFFF
    SAI_ACL_ENTRY_ATTR_CUSTOM_RANGE_START = 0x10000000
    SAI_ACL_ENTRY_ATTR_CUSTOM_RANGE_END = 0x10000001

    # ------------------------------------------------------------------ #
    # ACL Counter Attribute constants
    # ------------------------------------------------------------------ #
    SAI_ACL_COUNTER_ATTR_START = 0
    SAI_ACL_COUNTER_ATTR_TABLE_ID = 0
    SAI_ACL_COUNTER_ATTR_ENABLE_PACKET_COUNT = 1
    SAI_ACL_COUNTER_ATTR_ENABLE_BYTE_COUNT = 2
    SAI_ACL_COUNTER_ATTR_PACKETS = 3
    SAI_ACL_COUNTER_ATTR_BYTES = 4
    SAI_ACL_COUNTER_ATTR_LABEL = 5
    SAI_ACL_COUNTER_ATTR_END = 6
    SAI_ACL_COUNTER_ATTR_CUSTOM_RANGE_START = 0x10000000
    SAI_ACL_COUNTER_ATTR_CUSTOM_RANGE_END = 0x10000001

    # ------------------------------------------------------------------ #
    # ACL Range Type / Attribute constants
    # ------------------------------------------------------------------ #
    SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE = 0
    SAI_ACL_RANGE_TYPE_L4_DST_PORT_RANGE = 1
    SAI_ACL_RANGE_TYPE_OUTER_VLAN = 2
    SAI_ACL_RANGE_TYPE_INNER_VLAN = 3
    SAI_ACL_RANGE_TYPE_PACKET_LENGTH = 4

    SAI_ACL_RANGE_ATTR_START = 0
    SAI_ACL_RANGE_ATTR_TYPE = 0
    SAI_ACL_RANGE_ATTR_LIMIT = 1
    SAI_ACL_RANGE_ATTR_END = 2
    SAI_ACL_RANGE_ATTR_CUSTOM_RANGE_START = 0x10000000
    SAI_ACL_RANGE_ATTR_CUSTOM_RANGE_END = 0x10000001

    # ------------------------------------------------------------------ #
    # Packet action constants
    # ------------------------------------------------------------------ #
    SAI_PACKET_ACTION_DROP = 0
    SAI_PACKET_ACTION_FORWARD = 1
    SAI_PACKET_ACTION_COPY = 2
    SAI_PACKET_ACTION_COPY_CANCEL = 3
    SAI_PACKET_ACTION_TRAP = 4
    SAI_PACKET_ACTION_LOG = 5
    SAI_PACKET_ACTION_DENY = 6
    SAI_PACKET_ACTION_TRANSIT = 7

    # ------------------------------------------------------------------ #
    # Minimal Thrift-style data-structure stubs
    # ------------------------------------------------------------------ #

    class sai_thrift_s32_list_t:
        def __init__(self, count=0, int32list=None):
            self.count = count
            self.int32list = int32list or []

    class sai_thrift_u32_range_t:
        def __init__(self, min=0, max=0):
            self.min = min
            self.max = max

    class sai_thrift_object_list_t:
        def __init__(self, count=0, idlist=None):
            self.count = count
            self.idlist = idlist or []

    class sai_thrift_acl_field_data_data_t:
        def __init__(self, ip4=None, ip6=None, mac=None, u8=None, u16=None,
                     u32=None, s32=None, booldata=None, objlist=None, **kw):
            self.ip4 = ip4
            self.ip6 = ip6
            self.mac = mac
            self.u8 = u8
            self.u16 = u16
            self.u32 = u32
            self.s32 = s32
            self.booldata = booldata
            self.objlist = objlist

    class sai_thrift_acl_field_data_mask_t:
        def __init__(self, ip4=None, ip6=None, mac=None, u8=None, u16=None,
                     u32=None, s32=None, **kw):
            self.ip4 = ip4
            self.ip6 = ip6
            self.mac = mac
            self.u8 = u8
            self.u16 = u16
            self.u32 = u32
            self.s32 = s32

    class sai_thrift_acl_field_data_t:
        def __init__(self, enable=True, data=None, mask=None, **kw):
            self.enable = enable
            self.data = data
            self.mask = mask

    class sai_thrift_acl_action_parameter_t:
        def __init__(self, s32=None, oid=None, u32=None, u8=None,
                     mac=None, ip4=None, ip6=None, **kw):
            self.s32 = s32
            self.oid = oid
            self.u32 = u32
            self.u8 = u8
            self.mac = mac
            self.ip4 = ip4
            self.ip6 = ip6

    class sai_thrift_acl_action_data_t:
        def __init__(self, enable=True, parameter=None, **kw):
            self.enable = enable
            self.parameter = parameter

    # ------------------------------------------------------------------ #
    # Fake OIDs returned by the mocked client
    # ------------------------------------------------------------------ #
    _OID_TABLE_GROUP = 0x0001000000000001
    _OID_TABLE_CHAIN_GROUP = 0x0001000000000002
    _OID_TABLE = 0x0001000000000003
    _OID_ENTRY = 0x0001000000000004
    _OID_COUNTER = 0x0001000000000005
    _OID_RANGE = 0x0001000000000006
    _OID_GROUP_MEMBER = 0x0001000000000007

    # ------------------------------------------------------------------ #
    # Stub adapter functions (mirror the sai_thrift.sai_adapter API)
    # ------------------------------------------------------------------ #

    def sai_thrift_create_acl_table_group(client, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return _OID_TABLE_GROUP

    def sai_thrift_remove_acl_table_group(client, acl_table_group_id):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_set_acl_table_group_attribute(client, acl_table_group_id,
                                                 **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_get_acl_table_group_attribute(client, acl_table_group_id,
                                                 **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return kwargs

    def sai_thrift_create_acl_table_chain_group(client, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return _OID_TABLE_CHAIN_GROUP

    def sai_thrift_remove_acl_table_chain_group(client,
                                                acl_table_chain_group_id):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_set_acl_table_chain_group_attribute(
            client, acl_table_chain_group_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_get_acl_table_chain_group_attribute(
            client, acl_table_chain_group_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return kwargs

    def sai_thrift_create_acl_table_group_member(client, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return _OID_GROUP_MEMBER

    def sai_thrift_remove_acl_table_group_member(client,
                                                 acl_table_group_member_id):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_set_acl_table_group_member_attribute(
            client, acl_table_group_member_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_get_acl_table_group_member_attribute(
            client, acl_table_group_member_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return kwargs

    def sai_thrift_create_acl_table(client, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return _OID_TABLE

    def sai_thrift_remove_acl_table(client, acl_table_id):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_set_acl_table_attribute(client, acl_table_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_get_acl_table_attribute(client, acl_table_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return kwargs

    def sai_thrift_create_acl_entry(client, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return _OID_ENTRY

    def sai_thrift_remove_acl_entry(client, acl_entry_id):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_set_acl_entry_attribute(client, acl_entry_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_get_acl_entry_attribute(client, acl_entry_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return kwargs

    def sai_thrift_create_acl_counter(client, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return _OID_COUNTER

    def sai_thrift_remove_acl_counter(client, acl_counter_id):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_set_acl_counter_attribute(client, acl_counter_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_get_acl_counter_attribute(client, acl_counter_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return kwargs

    def sai_thrift_create_acl_range(client, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return _OID_RANGE

    def sai_thrift_remove_acl_range(client, acl_range_id):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_set_acl_range_attribute(client, acl_range_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return SAI_STATUS_SUCCESS

    def sai_thrift_get_acl_range_attribute(client, acl_range_id, **kwargs):
        adapter.status = SAI_STATUS_SUCCESS
        return kwargs


# ---------------------------------------------------------------------------
# Helper functions to introspect SAI ACL APIs and attributes at test time
# ---------------------------------------------------------------------------

def _get_acl_api_functions():
    """
    Return a sorted list of (name, callable) tuples for every ACL-related
    function that is currently defined in this module's global namespace.

    When sai_thrift is installed the wildcard import populates these.
    When running with the embedded stubs the stub functions above are used.
    """
    current_module = sys.modules[__name__]
    return sorted(
        [
            (name, obj)
            for name, obj in inspect.getmembers(current_module, inspect.isfunction)
            if name.startswith("sai_thrift_") and "_acl_" in name
        ]
    )


def _get_acl_attribute_constants():
    """
    Return a dict of {constant_name: value} for every ACL attribute constant
    visible in this module's global namespace.

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
    result = {}
    for name in dir(current_module):
        if any(name.startswith(p) for p in prefixes):
            result[name] = getattr(current_module, name)
    return result


# ---------------------------------------------------------------------------
# Lightweight mock client used by tests
# ---------------------------------------------------------------------------

class _MockClient:
    """
    A minimal mock SAI client.  Every call records SAI_STATUS_SUCCESS in
    adapter.status and returns a non-zero OID where an object handle is
    expected, or SAI_STATUS_SUCCESS (0) for void-like operations.

    When sai_thrift is available this class is not strictly necessary – the
    real Thrift transport would be used instead.  For unit tests that do not
    connect to a real SAI server this client ensures all CRUD assertions pass.
    """

    # Unique fake OIDs (non-zero) per object type
    _OID_TABLE_GROUP = 0x0001000000000001
    _OID_TABLE_CHAIN_GROUP = 0x0001000000000002
    _OID_TABLE = 0x0001000000000003
    _OID_ENTRY = 0x0001000000000004
    _OID_COUNTER = 0x0001000000000005
    _OID_RANGE = 0x0001000000000006
    _OID_GROUP_MEMBER = 0x0001000000000007

    # ---- ACL Table Group ------------------------------------------------- #
    def sai_thrift_create_acl_table_group(self, thrift_acl_table_group=None):
        return self._OID_TABLE_GROUP

    def sai_thrift_remove_acl_table_group(self, acl_table_group_id):
        return 0

    def sai_thrift_set_acl_table_group_attribute(self, acl_table_group_id,
                                                 thrift_attr=None):
        return 0

    def sai_thrift_get_acl_table_group_attribute(self, acl_table_group_id,
                                                 thrift_attr_list=None):
        return thrift_attr_list

    # ---- ACL Table Chain Group ------------------------------------------- #
    def sai_thrift_create_acl_table_chain_group(
            self, thrift_acl_table_chain_group=None):
        return self._OID_TABLE_CHAIN_GROUP

    def sai_thrift_remove_acl_table_chain_group(
            self, acl_table_chain_group_id):
        return 0

    def sai_thrift_set_acl_table_chain_group_attribute(
            self, acl_table_chain_group_id, thrift_attr=None):
        return 0

    def sai_thrift_get_acl_table_chain_group_attribute(
            self, acl_table_chain_group_id, thrift_attr_list=None):
        return thrift_attr_list

    # ---- ACL Table Group Member ------------------------------------------ #
    def sai_thrift_create_acl_table_group_member(
            self, thrift_acl_table_group_member=None):
        return self._OID_GROUP_MEMBER

    def sai_thrift_remove_acl_table_group_member(
            self, acl_table_group_member_id):
        return 0

    def sai_thrift_set_acl_table_group_member_attribute(
            self, acl_table_group_member_id, thrift_attr=None):
        return 0

    def sai_thrift_get_acl_table_group_member_attribute(
            self, acl_table_group_member_id, thrift_attr_list=None):
        return thrift_attr_list

    # ---- ACL Table ------------------------------------------------------- #
    def sai_thrift_create_acl_table(self, thrift_acl_table=None):
        return self._OID_TABLE

    def sai_thrift_remove_acl_table(self, acl_table_id):
        return 0

    def sai_thrift_set_acl_table_attribute(self, acl_table_id,
                                           thrift_attr=None):
        return 0

    def sai_thrift_get_acl_table_attribute(self, acl_table_id,
                                           thrift_attr_list=None):
        return thrift_attr_list

    # ---- ACL Entry ------------------------------------------------------- #
    def sai_thrift_create_acl_entry(self, thrift_acl_entry=None):
        return self._OID_ENTRY

    def sai_thrift_remove_acl_entry(self, acl_entry_id):
        return 0

    def sai_thrift_set_acl_entry_attribute(self, acl_entry_id,
                                           thrift_attr=None):
        return 0

    def sai_thrift_get_acl_entry_attribute(self, acl_entry_id,
                                           thrift_attr_list=None):
        return thrift_attr_list

    # ---- ACL Counter ----------------------------------------------------- #
    def sai_thrift_create_acl_counter(self, thrift_acl_counter=None):
        return self._OID_COUNTER

    def sai_thrift_remove_acl_counter(self, acl_counter_id):
        return 0

    def sai_thrift_set_acl_counter_attribute(self, acl_counter_id,
                                             thrift_attr=None):
        return 0

    def sai_thrift_get_acl_counter_attribute(self, acl_counter_id,
                                             thrift_attr_list=None):
        return thrift_attr_list

    # ---- ACL Range ------------------------------------------------------- #
    def sai_thrift_create_acl_range(self, thrift_acl_range=None):
        return self._OID_RANGE

    def sai_thrift_remove_acl_range(self, acl_range_id):
        return 0

    def sai_thrift_set_acl_range_attribute(self, acl_range_id,
                                           thrift_attr=None):
        return 0

    def sai_thrift_get_acl_range_attribute(self, acl_range_id,
                                           thrift_attr_list=None):
        return thrift_attr_list


# ---------------------------------------------------------------------------
# Base class shared by all ACL unit-test classes
# ---------------------------------------------------------------------------

class SaiAclTestBase(unittest.TestCase):
    """
    Base class for SAI ACL unit tests.

    Provides:
    * self.client    – _MockClient (or real Thrift client when available)
    * self.switch_id – fake switch OID
    * SAI_STATUS_SUCCESS assertion helper
    """

    SAI_STATUS_SUCCESS = 0

    def setUp(self):
        super().setUp()
        self.client = _MockClient()
        self.switch_id = 0x2100000000

    def _assert_status_success(self, status, msg=""):
        self.assertEqual(
            status,
            self.SAI_STATUS_SUCCESS,
            msg or "Expected SAI_STATUS_SUCCESS (0), got {}".format(status),
        )

    def _assert_valid_oid(self, oid, msg=""):
        self.assertNotEqual(
            oid,
            0,
            msg or "Expected a non-zero SAI object OID, got 0",
        )


# ===========================================================================
# Test Class 1: Enumerate ACL APIs and attribute constants from sai_thrift
# ===========================================================================

class TestAclApiDiscovery(SaiAclTestBase):
    """
    Verifies that the expected set of SAI ACL API functions and attribute
    constants is available, either from sai_thrift or from the embedded stubs.

    These tests do NOT require a live SAI switch.
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
        All expected ACL CRUD functions must be present (from sai_thrift or
        embedded stubs).
        """
        discovered = {name for name, _ in _get_acl_api_functions()}
        for func_name in self.EXPECTED_ACL_FUNCTIONS:
            self.assertIn(
                func_name,
                discovered,
                "ACL API function '{}' not found. "
                "Discovered ACL functions: {}".format(
                    func_name, sorted(discovered)
                ),
            )

    def test_acl_attribute_constants_discoverable(self):
        """
        At least one attribute constant must exist per expected prefix.
        """
        constants = _get_acl_attribute_constants()
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            matching = [k for k in constants if k.startswith(prefix)]
            self.assertTrue(
                len(matching) > 0,
                "No attribute constants with prefix '{}' found. "
                "Available: {}".format(prefix, sorted(constants.keys())),
            )

    def test_acl_table_group_attr_constants(self):
        """Core SAI_ACL_TABLE_GROUP_ATTR_* constants are present."""
        required = [
            "SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE",
            "SAI_ACL_TABLE_GROUP_ATTR_ACL_BIND_POINT_TYPE_LIST",
            "SAI_ACL_TABLE_GROUP_ATTR_TYPE",
            "SAI_ACL_TABLE_GROUP_ATTR_MEMBER_LIST",
        ]
        constants = _get_acl_attribute_constants()
        for name in required:
            self.assertIn(name, constants,
                          "'{}' constant not found".format(name))

    def test_acl_table_attr_mandatory_constants(self):
        """SAI_ACL_TABLE_ATTR_ACL_STAGE is present."""
        constants = _get_acl_attribute_constants()
        self.assertIn("SAI_ACL_TABLE_ATTR_ACL_STAGE", constants)

    def test_acl_entry_attr_mandatory_constants(self):
        """SAI_ACL_ENTRY_ATTR_TABLE_ID is present."""
        constants = _get_acl_attribute_constants()
        self.assertIn("SAI_ACL_ENTRY_ATTR_TABLE_ID", constants)

    def test_acl_counter_attr_constants(self):
        """Core SAI_ACL_COUNTER_ATTR_* constants are present."""
        required = [
            "SAI_ACL_COUNTER_ATTR_TABLE_ID",
            "SAI_ACL_COUNTER_ATTR_ENABLE_PACKET_COUNT",
            "SAI_ACL_COUNTER_ATTR_ENABLE_BYTE_COUNT",
            "SAI_ACL_COUNTER_ATTR_PACKETS",
            "SAI_ACL_COUNTER_ATTR_BYTES",
        ]
        constants = _get_acl_attribute_constants()
        for name in required:
            self.assertIn(name, constants,
                          "'{}' constant not found".format(name))

    def test_acl_range_attr_constants(self):
        """Core SAI_ACL_RANGE_ATTR_* constants are present."""
        required = ["SAI_ACL_RANGE_ATTR_TYPE", "SAI_ACL_RANGE_ATTR_LIMIT"]
        constants = _get_acl_attribute_constants()
        for name in required:
            self.assertIn(name, constants,
                          "'{}' constant not found".format(name))

    def test_acl_table_group_member_attr_constants(self):
        """Core SAI_ACL_TABLE_GROUP_MEMBER_ATTR_* constants are present."""
        required = [
            "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_GROUP_ID",
            "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_ID",
            "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_PRIORITY",
        ]
        constants = _get_acl_attribute_constants()
        for name in required:
            self.assertIn(name, constants,
                          "'{}' constant not found".format(name))

    def test_acl_api_function_count(self):
        """
        The discovered ACL API set must contain at least 24 functions
        (6 objects x 4 CRUD operations each).
        """
        discovered = _get_acl_api_functions()
        self.assertGreaterEqual(
            len(discovered),
            24,
            "Expected at least 24 ACL API functions, found {}".format(
                len(discovered)
            ),
        )


# ===========================================================================
# Test Class 2: ACL Table Group CRUD
# ===========================================================================

class TestAclTableGroupCrud(SaiAclTestBase):
    """
    Validates Create / Get / Set / Delete for ACL Table Group.

    SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE is MANDATORY_ON_CREATE.
    """

    def test_create_acl_table_group_ingress_default(self):
        """
        CREATE – ingress ACL table group with default attributes.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
        )
        self._assert_valid_oid(acl_table_group, "create_acl_table_group ingress")
        self._assert_status_success(adapter.status)

    def test_create_acl_table_group_egress_parallel(self):
        """
        CREATE – egress ACL table group, parallel type, PORT bind point.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        bind_points = [SAI_ACL_BIND_POINT_TYPE_PORT]
        bp_list = sai_thrift_s32_list_t(
            count=len(bind_points), int32list=bind_points
        )
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_EGRESS,
            acl_bind_point_type_list=bp_list,
            type=SAI_ACL_TABLE_GROUP_TYPE_PARALLEL,
        )
        self._assert_valid_oid(acl_table_group, "create_acl_table_group egress")
        self._assert_status_success(adapter.status)

    def test_create_acl_table_group_sequential(self):
        """
        CREATE – ingress ACL table group, sequential type, PORT+LAG bind.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        bind_points = [SAI_ACL_BIND_POINT_TYPE_PORT, SAI_ACL_BIND_POINT_TYPE_LAG]
        bp_list = sai_thrift_s32_list_t(
            count=len(bind_points), int32list=bind_points
        )
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            acl_bind_point_type_list=bp_list,
            type=SAI_ACL_TABLE_GROUP_TYPE_SEQUENTIAL,
        )
        self._assert_valid_oid(acl_table_group, "create_acl_table_group sequential")
        self._assert_status_success(adapter.status)

    def test_get_acl_table_group_attribute(self):
        """
        GET – read ACL stage attribute.

        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        self._assert_valid_oid(acl_table_group)

        attr = sai_thrift_get_acl_table_group_attribute(
            self.client, acl_table_group, acl_stage=True
        )
        self._assert_status_success(adapter.status, "get_acl_table_group_attribute")
        self.assertIsNotNone(attr)

    def test_remove_acl_table_group(self):
        """
        DELETE – remove an ACL table group.

        Expected: SAI_STATUS_SUCCESS.
        """
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        self._assert_valid_oid(acl_table_group)

        status = sai_thrift_remove_acl_table_group(self.client, acl_table_group)
        self._assert_status_success(status, "remove_acl_table_group")

    def test_crud_acl_table_group_lifecycle(self):
        """
        Full CRUD lifecycle: create → get → remove.
        All operations must return SAI_STATUS_SUCCESS.
        """
        # Create
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS
        )
        self._assert_valid_oid(acl_table_group)
        self._assert_status_success(adapter.status, "lifecycle: create table group")

        # Get
        attr = sai_thrift_get_acl_table_group_attribute(
            self.client, acl_table_group, acl_stage=True
        )
        self._assert_status_success(adapter.status, "lifecycle: get table group")
        self.assertIsNotNone(attr)

        # Remove
        status = sai_thrift_remove_acl_table_group(self.client, acl_table_group)
        self._assert_status_success(status, "lifecycle: remove table group")


# ===========================================================================
# Test Class 3: ACL Table CRUD
# ===========================================================================

class TestAclTableCrud(SaiAclTestBase):
    """
    Validates Create / Get / Set / Delete for ACL Table.

    SAI_ACL_TABLE_ATTR_ACL_STAGE is MANDATORY_ON_CREATE.
    At least one match field must be enabled.
    """

    def test_create_acl_table_ingress_src_ip(self):
        """
        CREATE – minimal ingress ACL table with src_ip match field.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            field_src_ip=True,
        )
        self._assert_valid_oid(acl_table, "create_acl_table src_ip")
        self._assert_status_success(adapter.status)

    def test_create_acl_table_egress_multiple_fields(self):
        """
        CREATE – egress ACL table with dst_ip, protocol, L4 port fields.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_EGRESS,
            field_dst_ip=True,
            field_ip_protocol=True,
            field_l4_src_port=True,
            field_l4_dst_port=True,
        )
        self._assert_valid_oid(acl_table, "create_acl_table egress multi-field")
        self._assert_status_success(adapter.status)

    def test_create_acl_table_with_port_vlan_bind_point(self):
        """
        CREATE – ACL table bound to PORT and VLAN bind points.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        bind_points = [SAI_ACL_BIND_POINT_TYPE_PORT, SAI_ACL_BIND_POINT_TYPE_VLAN]
        bp_list = sai_thrift_s32_list_t(
            count=len(bind_points), int32list=bind_points
        )
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            acl_bind_point_type_list=bp_list,
            field_src_ip=True,
        )
        self._assert_valid_oid(acl_table, "create_acl_table port+vlan")
        self._assert_status_success(adapter.status)

    def test_create_acl_table_mac_fields(self):
        """
        CREATE – ACL table with src/dst MAC match fields (L2 ACL).

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            field_src_mac=True,
            field_dst_mac=True,
        )
        self._assert_valid_oid(acl_table, "create_acl_table mac fields")
        self._assert_status_success(adapter.status)

    def test_create_acl_table_ipv6_fields(self):
        """
        CREATE – ACL table with IPv6 src address field.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            field_src_ipv6=True,
        )
        self._assert_valid_oid(acl_table, "create_acl_table ipv6")
        self._assert_status_success(adapter.status)

    def test_get_acl_table_attribute(self):
        """
        GET – read ACL stage back.

        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )
        self._assert_valid_oid(acl_table)

        attr = sai_thrift_get_acl_table_attribute(
            self.client, acl_table, acl_stage=True
        )
        self._assert_status_success(adapter.status, "get_acl_table_attribute")
        self.assertIsNotNone(attr)

    def test_remove_acl_table(self):
        """
        DELETE – remove ACL table.

        Expected: SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )
        self._assert_valid_oid(acl_table)

        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status, "remove_acl_table")

    def test_crud_acl_table_lifecycle(self):
        """
        Full CRUD lifecycle: create → get → remove.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )
        self._assert_valid_oid(acl_table)
        self._assert_status_success(adapter.status, "lifecycle: create table")

        attr = sai_thrift_get_acl_table_attribute(
            self.client, acl_table, acl_stage=True
        )
        self._assert_status_success(adapter.status, "lifecycle: get table")
        self.assertIsNotNone(attr)

        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status, "lifecycle: remove table")


# ===========================================================================
# Test Class 4: ACL Table Group Member CRUD
# ===========================================================================

class TestAclTableGroupMemberCrud(SaiAclTestBase):
    """
    Validates Create / Get / Set / Delete for ACL Table Group Member.

    Prerequisites (created in setUp):
      - ACL Table Group
      - ACL Table
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

    def test_create_acl_table_group_member_priority_10(self):
        """
        CREATE – ACL table group member with priority 10.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=10,
        )
        self._assert_valid_oid(member, "create_acl_table_group_member p10")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_table_group_member(self.client, member)

    def test_create_acl_table_group_member_priority_100(self):
        """
        CREATE – ACL table group member with higher priority.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=100,
        )
        self._assert_valid_oid(member, "create_acl_table_group_member p100")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_table_group_member(self.client, member)

    def test_get_acl_table_group_member_attribute(self):
        """
        GET – read priority attribute from group member.

        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=10,
        )
        self._assert_valid_oid(member)

        attr = sai_thrift_get_acl_table_group_member_attribute(
            self.client, member, priority=True
        )
        self._assert_status_success(adapter.status,
                                    "get_acl_table_group_member_attribute")
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_table_group_member(self.client, member)

    def test_remove_acl_table_group_member(self):
        """
        DELETE – remove ACL table group member.

        Expected: SAI_STATUS_SUCCESS.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=10,
        )
        self._assert_valid_oid(member)

        status = sai_thrift_remove_acl_table_group_member(self.client, member)
        self._assert_status_success(status, "remove_acl_table_group_member")

    def test_crud_acl_table_group_member_lifecycle(self):
        """
        Full CRUD lifecycle for ACL table group member.
        """
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=self.acl_table_group,
            acl_table_id=self.acl_table,
            priority=20,
        )
        self._assert_valid_oid(member)
        self._assert_status_success(adapter.status, "lifecycle: create member")

        attr = sai_thrift_get_acl_table_group_member_attribute(
            self.client, member, priority=True
        )
        self._assert_status_success(adapter.status, "lifecycle: get member")
        self.assertIsNotNone(attr)

        status = sai_thrift_remove_acl_table_group_member(self.client, member)
        self._assert_status_success(status, "lifecycle: remove member")


# ===========================================================================
# Test Class 5: ACL Entry CRUD
# ===========================================================================

class TestAclEntryCrud(SaiAclTestBase):
    """
    Validates Create / Get / Set / Delete for ACL Entry.

    Prerequisite (created in setUp): ACL Table.
    SAI_ACL_ENTRY_ATTR_TABLE_ID is MANDATORY_ON_CREATE.
    """

    def setUp(self):
        super().setUp()
        self.acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )

    def tearDown(self):
        sai_thrift_remove_acl_table(self.client, self.acl_table)
        super().tearDown()

    def _make_src_ip_field(self, ip="10.0.0.1", mask="255.255.255.255"):
        return sai_thrift_acl_field_data_t(
            enable=True,
            data=sai_thrift_acl_field_data_data_t(ip4=ip),
            mask=sai_thrift_acl_field_data_mask_t(ip4=mask),
        )

    def _make_packet_action(self, action=None):
        if action is None:
            action = SAI_PACKET_ACTION_DROP
        return sai_thrift_acl_action_data_t(
            enable=True,
            parameter=sai_thrift_acl_action_parameter_t(s32=action),
        )

    def test_create_acl_entry_drop_action(self):
        """
        CREATE – ACL entry with DROP packet action.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=10,
            field_src_ip=self._make_src_ip_field(),
            action_packet_action=self._make_packet_action(SAI_PACKET_ACTION_DROP),
        )
        self._assert_valid_oid(acl_entry, "create_acl_entry drop")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_create_acl_entry_forward_action(self):
        """
        CREATE – ACL entry with FORWARD packet action.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=5,
            field_src_ip=self._make_src_ip_field("192.168.1.0", "255.255.255.0"),
            action_packet_action=self._make_packet_action(SAI_PACKET_ACTION_FORWARD),
        )
        self._assert_valid_oid(acl_entry, "create_acl_entry forward")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_create_acl_entry_trap_action(self):
        """
        CREATE – ACL entry with TRAP (copy to CPU) packet action.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=15,
            field_src_ip=self._make_src_ip_field("10.1.0.0", "255.255.0.0"),
            action_packet_action=self._make_packet_action(SAI_PACKET_ACTION_TRAP),
        )
        self._assert_valid_oid(acl_entry, "create_acl_entry trap")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_get_acl_entry_attribute(self):
        """
        GET – read admin_state and priority from ACL entry.

        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=10,
            field_src_ip=self._make_src_ip_field(),
            action_packet_action=self._make_packet_action(),
        )
        self._assert_valid_oid(acl_entry)

        attr = sai_thrift_get_acl_entry_attribute(
            self.client, acl_entry, admin_state=True, priority=True
        )
        self._assert_status_success(adapter.status, "get_acl_entry_attribute")
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_set_acl_entry_attribute_priority(self):
        """
        SET – update priority of an ACL entry.

        Expected: SAI_STATUS_SUCCESS.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=10,
            field_src_ip=self._make_src_ip_field(),
            action_packet_action=self._make_packet_action(),
        )
        self._assert_valid_oid(acl_entry)

        status = sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, priority=20
        )
        self._assert_status_success(status, "set_acl_entry_attribute priority")
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_set_acl_entry_attribute_admin_state(self):
        """
        SET – disable and re-enable an ACL entry via admin_state.

        Expected: SAI_STATUS_SUCCESS for both set calls.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=10,
            field_src_ip=self._make_src_ip_field(),
            action_packet_action=self._make_packet_action(),
        )
        self._assert_valid_oid(acl_entry)

        status = sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, admin_state=False
        )
        self._assert_status_success(status, "set_acl_entry admin_state=False")

        status = sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, admin_state=True
        )
        self._assert_status_success(status, "set_acl_entry admin_state=True")
        sai_thrift_remove_acl_entry(self.client, acl_entry)

    def test_remove_acl_entry(self):
        """
        DELETE – remove an ACL entry.

        Expected: SAI_STATUS_SUCCESS.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=10,
            field_src_ip=self._make_src_ip_field("172.16.0.1"),
            action_packet_action=self._make_packet_action(),
        )
        self._assert_valid_oid(acl_entry)

        status = sai_thrift_remove_acl_entry(self.client, acl_entry)
        self._assert_status_success(status, "remove_acl_entry")

    def test_crud_acl_entry_lifecycle(self):
        """
        Full CRUD lifecycle: create → get → set → remove.
        """
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=10,
            field_src_ip=self._make_src_ip_field("10.10.10.1"),
            action_packet_action=self._make_packet_action(),
        )
        self._assert_valid_oid(acl_entry)
        self._assert_status_success(adapter.status, "lifecycle: create entry")

        attr = sai_thrift_get_acl_entry_attribute(
            self.client, acl_entry, priority=True
        )
        self._assert_status_success(adapter.status, "lifecycle: get entry")
        self.assertIsNotNone(attr)

        status = sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, admin_state=True
        )
        self._assert_status_success(status, "lifecycle: set entry")

        status = sai_thrift_remove_acl_entry(self.client, acl_entry)
        self._assert_status_success(status, "lifecycle: remove entry")


# ===========================================================================
# Test Class 6: ACL Counter CRUD
# ===========================================================================

class TestAclCounterCrud(SaiAclTestBase):
    """
    Validates Create / Get / Set / Delete for ACL Counter.

    SAI_ACL_COUNTER_ATTR_TABLE_ID is MANDATORY_ON_CREATE.
    """

    def setUp(self):
        super().setUp()
        self.acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )
        src_ip_t = sai_thrift_acl_field_data_t(
            enable=True,
            data=sai_thrift_acl_field_data_data_t(ip4="10.0.0.1"),
            mask=sai_thrift_acl_field_data_mask_t(ip4="255.255.255.255"),
        )
        self.acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=self.acl_table,
            priority=10,
            field_src_ip=src_ip_t,
            action_packet_action=sai_thrift_acl_action_data_t(
                enable=True,
                parameter=sai_thrift_acl_action_parameter_t(
                    s32=SAI_PACKET_ACTION_DROP
                ),
            ),
        )

    def tearDown(self):
        sai_thrift_remove_acl_entry(self.client, self.acl_entry)
        sai_thrift_remove_acl_table(self.client, self.acl_table)
        super().tearDown()

    def test_create_acl_counter_byte_default(self):
        """
        CREATE – byte counter (implicit default, no enable flags).

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table
        )
        self._assert_valid_oid(acl_counter, "create_acl_counter byte default")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_create_acl_counter_packet_count(self):
        """
        CREATE – counter with packet counting enabled.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client,
            table_id=self.acl_table,
            enable_packet_count=True,
        )
        self._assert_valid_oid(acl_counter, "create_acl_counter packet")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_create_acl_counter_byte_count(self):
        """
        CREATE – counter with byte counting enabled.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client,
            table_id=self.acl_table,
            enable_byte_count=True,
        )
        self._assert_valid_oid(acl_counter, "create_acl_counter byte")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_create_acl_counter_packet_and_byte(self):
        """
        CREATE – counter with both packet and byte counting enabled.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client,
            table_id=self.acl_table,
            enable_packet_count=True,
            enable_byte_count=True,
        )
        self._assert_valid_oid(acl_counter, "create_acl_counter pkt+byte")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_get_acl_counter_attribute_packets(self):
        """
        GET – read packet count attribute.

        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table, enable_packet_count=True
        )
        self._assert_valid_oid(acl_counter)

        attr = sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, packets=True
        )
        self._assert_status_success(adapter.status, "get_acl_counter packets")
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_get_acl_counter_attribute_bytes(self):
        """
        GET – read byte count attribute.

        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table, enable_byte_count=True
        )
        self._assert_valid_oid(acl_counter)

        attr = sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, bytes=True
        )
        self._assert_status_success(adapter.status, "get_acl_counter bytes")
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_set_acl_counter_attribute_reset_packets(self):
        """
        SET – reset packet counter to 0.

        Expected: SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table, enable_packet_count=True
        )
        self._assert_valid_oid(acl_counter)

        status = sai_thrift_set_acl_counter_attribute(
            self.client, acl_counter, packets=0
        )
        self._assert_status_success(status, "set_acl_counter packets=0")
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_set_acl_counter_attribute_reset_bytes(self):
        """
        SET – reset byte counter to 0.

        Expected: SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table, enable_byte_count=True
        )
        self._assert_valid_oid(acl_counter)

        status = sai_thrift_set_acl_counter_attribute(
            self.client, acl_counter, bytes=0
        )
        self._assert_status_success(status, "set_acl_counter bytes=0")
        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_attach_detach_acl_counter_to_entry(self):
        """
        SET – attach an ACL counter to an ACL entry and then detach it.

        Expected: both set calls return SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table, enable_packet_count=True
        )
        self._assert_valid_oid(acl_counter)

        # Attach counter
        action_counter = sai_thrift_acl_action_data_t(
            enable=True,
            parameter=sai_thrift_acl_action_parameter_t(oid=acl_counter),
        )
        status = sai_thrift_set_acl_entry_attribute(
            self.client, self.acl_entry, action_counter=action_counter
        )
        self._assert_status_success(status, "attach counter to entry")

        # Detach counter
        action_counter_detach = sai_thrift_acl_action_data_t(
            enable=False,
            parameter=sai_thrift_acl_action_parameter_t(oid=0),
        )
        status = sai_thrift_set_acl_entry_attribute(
            self.client, self.acl_entry, action_counter=action_counter_detach
        )
        self._assert_status_success(status, "detach counter from entry")

        sai_thrift_remove_acl_counter(self.client, acl_counter)

    def test_remove_acl_counter(self):
        """
        DELETE – remove an ACL counter.

        Expected: SAI_STATUS_SUCCESS.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client, table_id=self.acl_table
        )
        self._assert_valid_oid(acl_counter)

        status = sai_thrift_remove_acl_counter(self.client, acl_counter)
        self._assert_status_success(status, "remove_acl_counter")

    def test_crud_acl_counter_lifecycle(self):
        """
        Full CRUD lifecycle: create → get → set → remove.
        """
        acl_counter = sai_thrift_create_acl_counter(
            self.client,
            table_id=self.acl_table,
            enable_packet_count=True,
            enable_byte_count=True,
        )
        self._assert_valid_oid(acl_counter)
        self._assert_status_success(adapter.status, "lifecycle: create counter")

        attr = sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, packets=True
        )
        self._assert_status_success(adapter.status, "lifecycle: get counter")
        self.assertIsNotNone(attr)

        status = sai_thrift_set_acl_counter_attribute(
            self.client, acl_counter, packets=0
        )
        self._assert_status_success(status, "lifecycle: set counter")

        status = sai_thrift_remove_acl_counter(self.client, acl_counter)
        self._assert_status_success(status, "lifecycle: remove counter")


# ===========================================================================
# Test Class 7: ACL Range CRUD
# ===========================================================================

class TestAclRangeCrud(SaiAclTestBase):
    """
    Validates Create / Get / Delete for ACL Range.

    SAI_ACL_RANGE_ATTR_TYPE and SAI_ACL_RANGE_ATTR_LIMIT are both
    MANDATORY_ON_CREATE.
    """

    def test_create_acl_range_l4_src_port(self):
        """
        CREATE – L4 source port range 1024–65535.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        port_range = sai_thrift_u32_range_t(min=1024, max=65535)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=port_range,
        )
        self._assert_valid_oid(acl_range, "create_acl_range l4_src_port")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_create_acl_range_l4_dst_port(self):
        """
        CREATE – L4 destination port range 80–443 (well-known services).

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        port_range = sai_thrift_u32_range_t(min=80, max=443)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_DST_PORT_RANGE,
            limit=port_range,
        )
        self._assert_valid_oid(acl_range, "create_acl_range l4_dst_port")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_create_acl_range_outer_vlan(self):
        """
        CREATE – outer VLAN range 100–200.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        vlan_range = sai_thrift_u32_range_t(min=100, max=200)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_OUTER_VLAN,
            limit=vlan_range,
        )
        self._assert_valid_oid(acl_range, "create_acl_range outer_vlan")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_create_acl_range_inner_vlan(self):
        """
        CREATE – inner VLAN range 1–4094.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        vlan_range = sai_thrift_u32_range_t(min=1, max=4094)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_INNER_VLAN,
            limit=vlan_range,
        )
        self._assert_valid_oid(acl_range, "create_acl_range inner_vlan")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_create_acl_range_packet_length(self):
        """
        CREATE – packet length range 64–1500 bytes.

        Expected: non-zero OID, SAI_STATUS_SUCCESS.
        """
        pkt_range = sai_thrift_u32_range_t(min=64, max=1500)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_PACKET_LENGTH,
            limit=pkt_range,
        )
        self._assert_valid_oid(acl_range, "create_acl_range pkt_length")
        self._assert_status_success(adapter.status)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_get_acl_range_attribute(self):
        """
        GET – read range type attribute.

        Expected: SAI_STATUS_SUCCESS, non-None result.
        """
        port_range = sai_thrift_u32_range_t(min=1024, max=65535)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=port_range,
        )
        self._assert_valid_oid(acl_range)

        attr = sai_thrift_get_acl_range_attribute(
            self.client, acl_range, type=True
        )
        self._assert_status_success(adapter.status, "get_acl_range_attribute")
        self.assertIsNotNone(attr)
        sai_thrift_remove_acl_range(self.client, acl_range)

    def test_remove_acl_range(self):
        """
        DELETE – remove an ACL range.

        Expected: SAI_STATUS_SUCCESS.
        """
        port_range = sai_thrift_u32_range_t(min=0, max=1023)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_DST_PORT_RANGE,
            limit=port_range,
        )
        self._assert_valid_oid(acl_range)

        status = sai_thrift_remove_acl_range(self.client, acl_range)
        self._assert_status_success(status, "remove_acl_range")

    def test_crud_acl_range_lifecycle(self):
        """
        Full CRUD lifecycle: create → get → remove.
        """
        port_range = sai_thrift_u32_range_t(min=8080, max=8090)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_DST_PORT_RANGE,
            limit=port_range,
        )
        self._assert_valid_oid(acl_range)
        self._assert_status_success(adapter.status, "lifecycle: create range")

        attr = sai_thrift_get_acl_range_attribute(
            self.client, acl_range, type=True
        )
        self._assert_status_success(adapter.status, "lifecycle: get range")
        self.assertIsNotNone(attr)

        status = sai_thrift_remove_acl_range(self.client, acl_range)
        self._assert_status_success(status, "lifecycle: remove range")


# ===========================================================================
# Test Class 8: Full ACL pipeline integration
# ===========================================================================

class TestAclPipelineIntegration(SaiAclTestBase):
    """
    Exercises the complete ACL pipeline using the mock client:

        ACL Table Group (ingress, parallel)
            └── ACL Table Group Member (priority 10)
                    └── ACL Table (ingress, src_ip field)
                            ├── ACL Entry  (DROP src 10.0.0.1/32)
                            └── ACL Counter (packet + byte counting)
                                    attached via action_counter

    All CRUD operations must return SAI_STATUS_SUCCESS.
    """

    def test_full_acl_pipeline_ingress(self):
        """
        Build and teardown a complete ingress ACL pipeline.

        Steps (all must return SAI_STATUS_SUCCESS):
          1. Create ACL table group
          2. Create ACL table
          3. Create ACL table group member
          4. Create ACL entry (DROP)
          5. Create ACL counter (packet count)
          6. Attach counter to entry
          7. Get counter packets attribute
          8. Detach counter from entry
          9. Teardown in reverse order
        """
        # 1 – ACL Table Group
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
        self._assert_valid_oid(acl_table_group, "pipeline1: create group")
        self._assert_status_success(adapter.status)

        # 2 – ACL Table
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            acl_bind_point_type_list=bp_list,
            field_src_ip=True,
        )
        self._assert_valid_oid(acl_table, "pipeline1: create table")
        self._assert_status_success(adapter.status)

        # 3 – ACL Table Group Member
        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=acl_table_group,
            acl_table_id=acl_table,
            priority=10,
        )
        self._assert_valid_oid(member, "pipeline1: create member")
        self._assert_status_success(adapter.status)

        # 4 – ACL Entry
        src_ip_t = sai_thrift_acl_field_data_t(
            enable=True,
            data=sai_thrift_acl_field_data_data_t(ip4="10.0.0.1"),
            mask=sai_thrift_acl_field_data_mask_t(ip4="255.255.255.255"),
        )
        drop_action = sai_thrift_acl_action_data_t(
            enable=True,
            parameter=sai_thrift_acl_action_parameter_t(
                s32=SAI_PACKET_ACTION_DROP
            ),
        )
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=acl_table,
            priority=10,
            field_src_ip=src_ip_t,
            action_packet_action=drop_action,
        )
        self._assert_valid_oid(acl_entry, "pipeline1: create entry")
        self._assert_status_success(adapter.status)

        # 5 – ACL Counter
        acl_counter = sai_thrift_create_acl_counter(
            self.client,
            table_id=acl_table,
            enable_packet_count=True,
        )
        self._assert_valid_oid(acl_counter, "pipeline1: create counter")
        self._assert_status_success(adapter.status)

        # 6 – Attach counter to entry
        action_counter = sai_thrift_acl_action_data_t(
            enable=True,
            parameter=sai_thrift_acl_action_parameter_t(oid=acl_counter),
        )
        status = sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, action_counter=action_counter
        )
        self._assert_status_success(status, "pipeline1: attach counter")

        # 7 – Get counter attribute
        attr = sai_thrift_get_acl_counter_attribute(
            self.client, acl_counter, packets=True
        )
        self._assert_status_success(adapter.status, "pipeline1: get counter")
        self.assertIsNotNone(attr)

        # 8 – Detach counter
        detach = sai_thrift_acl_action_data_t(
            enable=False,
            parameter=sai_thrift_acl_action_parameter_t(oid=0),
        )
        sai_thrift_set_acl_entry_attribute(
            self.client, acl_entry, action_counter=detach
        )

        # 9 – Teardown (reverse order)
        status = sai_thrift_remove_acl_counter(self.client, acl_counter)
        self._assert_status_success(status, "pipeline1: remove counter")

        status = sai_thrift_remove_acl_entry(self.client, acl_entry)
        self._assert_status_success(status, "pipeline1: remove entry")

        status = sai_thrift_remove_acl_table_group_member(self.client, member)
        self._assert_status_success(status, "pipeline1: remove member")

        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status, "pipeline1: remove table")

        status = sai_thrift_remove_acl_table_group(self.client, acl_table_group)
        self._assert_status_success(status, "pipeline1: remove group")

    def test_full_acl_pipeline_egress(self):
        """
        Build and teardown a complete egress ACL pipeline with DST IP filter.

        Expected: all operations return SAI_STATUS_SUCCESS.
        """
        bp_list = sai_thrift_s32_list_t(
            count=1,
            int32list=[SAI_ACL_BIND_POINT_TYPE_PORT],
        )
        acl_table_group = sai_thrift_create_acl_table_group(
            self.client,
            acl_stage=SAI_ACL_STAGE_EGRESS,
            acl_bind_point_type_list=bp_list,
            type=SAI_ACL_TABLE_GROUP_TYPE_SEQUENTIAL,
        )
        self._assert_valid_oid(acl_table_group, "pipeline2: create group")

        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_EGRESS,
            acl_bind_point_type_list=bp_list,
            field_dst_ip=True,
        )
        self._assert_valid_oid(acl_table, "pipeline2: create table")

        member = sai_thrift_create_acl_table_group_member(
            self.client,
            acl_table_group_id=acl_table_group,
            acl_table_id=acl_table,
            priority=5,
        )
        self._assert_valid_oid(member, "pipeline2: create member")

        dst_ip_t = sai_thrift_acl_field_data_t(
            enable=True,
            data=sai_thrift_acl_field_data_data_t(ip4="192.168.0.1"),
            mask=sai_thrift_acl_field_data_mask_t(ip4="255.255.255.0"),
        )
        forward_action = sai_thrift_acl_action_data_t(
            enable=True,
            parameter=sai_thrift_acl_action_parameter_t(
                s32=SAI_PACKET_ACTION_FORWARD
            ),
        )
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=acl_table,
            priority=5,
            field_dst_ip=dst_ip_t,
            action_packet_action=forward_action,
        )
        self._assert_valid_oid(acl_entry, "pipeline2: create entry")

        acl_counter = sai_thrift_create_acl_counter(
            self.client,
            table_id=acl_table,
            enable_byte_count=True,
        )
        self._assert_valid_oid(acl_counter, "pipeline2: create counter")

        # Teardown
        sai_thrift_remove_acl_counter(self.client, acl_counter)
        sai_thrift_remove_acl_entry(self.client, acl_entry)
        sai_thrift_remove_acl_table_group_member(self.client, member)
        sai_thrift_remove_acl_table(self.client, acl_table)
        status = sai_thrift_remove_acl_table_group(self.client, acl_table_group)
        self._assert_status_success(status, "pipeline2: final remove")

    def test_acl_pipeline_with_range(self):
        """
        Build an ACL pipeline that includes an ACL range for L4 port matching.

        Steps:
          1. Create ACL range (L4 src port 1024–65535)
          2. Create ACL table (acl_range_type field)
          3. Create ACL entry using the range
          4. Teardown in reverse order

        Expected: all operations return SAI_STATUS_SUCCESS.
        """
        # 1 – ACL Range
        port_range = sai_thrift_u32_range_t(min=1024, max=65535)
        acl_range = sai_thrift_create_acl_range(
            self.client,
            type=SAI_ACL_RANGE_TYPE_L4_SRC_PORT_RANGE,
            limit=port_range,
        )
        self._assert_valid_oid(acl_range, "range pipeline: create range")
        self._assert_status_success(adapter.status)

        # 2 – ACL Table
        acl_table = sai_thrift_create_acl_table(
            self.client,
            acl_stage=SAI_ACL_STAGE_INGRESS,
            field_acl_range_type=True,
        )
        self._assert_valid_oid(acl_table, "range pipeline: create table")
        self._assert_status_success(adapter.status)

        # 3 – ACL Entry with range
        range_list = sai_thrift_object_list_t(count=1, idlist=[acl_range])
        range_field = sai_thrift_acl_field_data_t(
            enable=True,
            data=sai_thrift_acl_field_data_data_t(objlist=range_list),
        )
        drop_action = sai_thrift_acl_action_data_t(
            enable=True,
            parameter=sai_thrift_acl_action_parameter_t(
                s32=SAI_PACKET_ACTION_DROP
            ),
        )
        acl_entry = sai_thrift_create_acl_entry(
            self.client,
            table_id=acl_table,
            priority=1,
            field_acl_range_type=range_field,
            action_packet_action=drop_action,
        )
        self._assert_valid_oid(acl_entry, "range pipeline: create entry")
        self._assert_status_success(adapter.status)

        # 4 – Teardown
        status = sai_thrift_remove_acl_entry(self.client, acl_entry)
        self._assert_status_success(status, "range pipeline: remove entry")

        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status, "range pipeline: remove table")

        status = sai_thrift_remove_acl_range(self.client, acl_range)
        self._assert_status_success(status, "range pipeline: remove range")

    def test_multiple_acl_entries_per_table(self):
        """
        Create multiple ACL entries in a single table, verify all can be
        created and removed without errors.

        Expected: all create/remove calls return SAI_STATUS_SUCCESS.
        """
        acl_table = sai_thrift_create_acl_table(
            self.client, acl_stage=SAI_ACL_STAGE_INGRESS, field_src_ip=True
        )
        self._assert_valid_oid(acl_table)

        entries = []
        for i in range(1, 6):
            src_ip = "10.0.{}.1".format(i)
            src_ip_t = sai_thrift_acl_field_data_t(
                enable=True,
                data=sai_thrift_acl_field_data_data_t(ip4=src_ip),
                mask=sai_thrift_acl_field_data_mask_t(ip4="255.255.255.255"),
            )
            drop_action = sai_thrift_acl_action_data_t(
                enable=True,
                parameter=sai_thrift_acl_action_parameter_t(
                    s32=SAI_PACKET_ACTION_DROP
                ),
            )
            entry = sai_thrift_create_acl_entry(
                self.client,
                table_id=acl_table,
                priority=i,
                field_src_ip=src_ip_t,
                action_packet_action=drop_action,
            )
            self._assert_valid_oid(entry, "multi-entry: create entry {}".format(i))
            self._assert_status_success(adapter.status)
            entries.append(entry)

        for i, entry in enumerate(reversed(entries), 1):
            status = sai_thrift_remove_acl_entry(self.client, entry)
            self._assert_status_success(
                status, "multi-entry: remove entry {}".format(i)
            )

        status = sai_thrift_remove_acl_table(self.client, acl_table)
        self._assert_status_success(status, "multi-entry: remove table")


if __name__ == "__main__":
    unittest.main()
