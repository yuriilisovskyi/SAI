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

"""SAI PTFv2 Unit Tests for FDB feature (saifdb.h)"""

from sai_base_test import ThriftInterface
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter
import sai_thrift.sai_headers as sai_headers
from sai_utils import get_mandatory_attrs_from_csv, verify_object_attributes, load_attr_defaults

_ATTR_DEFAULTS = load_attr_defaults()


class _AssertMixin:
    def _assert_status_success(self, status, msg=""):
        self.assertEqual(status, SAI_STATUS_SUCCESS,
                         msg or "Expected SAI_STATUS_SUCCESS, got {}".format(status))


class TestFdbEntryCrud(_AssertMixin, ThriftInterface):
    """
    FDB Entry uses a struct key (switch_id, mac_address, bv_id).
    Mandatory attr from CSV:
      SAI_FDB_ENTRY_ATTR_TYPE (default: SAI_FDB_ENTRY_TYPE_DYNAMIC)
    Non-CRUD: sai_thrift_flush_fdb_entries
    Prerequisites: switch_id, VLAN, bridge port.
    """

    def runTest(self):
        switch_id = sai_thrift_create_switch(
            self.client, init_switch=True, src_mac_address="00:77:66:55:44:00"
        )
        self._assert_status_success(adapter.status)

        vlan = sai_thrift_create_vlan(self.client, vlan_id=300)

        attr = sai_thrift_get_switch_attribute(self.client, number_of_active_ports=True)
        num_ports = attr["number_of_active_ports"]
        attr = sai_thrift_get_switch_attribute(
            self.client, port_list=sai_thrift_object_list_t(idlist=[], count=num_ports))
        port_id = attr["port_list"].idlist[0]

        bp_kwargs = {
            attr[len("SAI_BRIDGE_PORT_ATTR_"):].lower(): getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv("SAI_BRIDGE_PORT_ATTR_", _ATTR_DEFAULTS)
            for _, default, _ in [_ATTR_DEFAULTS[attr]] if default
        }
        bp_kwargs["port_id"] = port_id
        bridge_port = sai_thrift_create_bridge_port(self.client, **bp_kwargs)

        fdb_entry = sai_thrift_fdb_entry_t(
            switch_id=switch_id,
            mac_address="00:11:22:33:44:55",
            bv_id=vlan,
        )

        self.create_fdb_entry(fdb_entry, bridge_port)
        self.get_fdb_entry_attribute(fdb_entry)
        self.remove_fdb_entry(fdb_entry)
        self.flush_fdb_entries(bridge_port)

        sai_thrift_remove_bridge_port(self.client, bridge_port)
        sai_thrift_remove_vlan(self.client, vlan)

    def create_fdb_entry(self, fdb_entry, bridge_port):
        mandatory = get_mandatory_attrs_from_csv("SAI_FDB_ENTRY_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_FDB_ENTRY_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["bridge_port_id"] = bridge_port
        status = sai_thrift_create_fdb_entry(self.client, fdb_entry, **kwargs)
        self._assert_status_success(status)

    def get_fdb_entry_attribute(self, fdb_entry):
        verify_object_attributes(self, sai_thrift_get_fdb_entry_attribute, fdb_entry, "SAI_FDB_ENTRY_ATTR_")

    def remove_fdb_entry(self, fdb_entry):
        status = sai_thrift_remove_fdb_entry(self.client, fdb_entry)
        self._assert_status_success(status)

    def flush_fdb_entries(self, bridge_port):
        """sai_thrift_flush_fdb_entries – expected SAI_STATUS_SUCCESS."""
        status = sai_thrift_flush_fdb_entries(
            self.client,
            bridge_port_id=bridge_port,
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_DYNAMIC,
        )
        self._assert_status_success(status)
