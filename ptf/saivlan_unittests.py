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

"""SAI PTFv2 Unit Tests for VLAN feature (saivlan.h)"""

from sai_base_test import ThriftInterface
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter
import sai_thrift.sai_headers as sai_headers
from sai_utils import get_mandatory_attrs_from_csv, verify_object_attributes, load_attr_defaults, get_non_crud_apis

_ATTR_DEFAULTS = load_attr_defaults()


class _AssertMixin:
    def _assert_status_success(self, status, msg=""):
        self.assertEqual(status, SAI_STATUS_SUCCESS,
                         msg or "Expected SAI_STATUS_SUCCESS, got {}".format(status))


class TestVlanCrud(_AssertMixin, ThriftInterface):
    """
    VLAN mandatory attrs from CSV: SAI_VLAN_ATTR_VLAN_ID (uint16, no default)
    Non-CRUD: sai_thrift_get_vlan_stats
    """

    def runTest(self):
        vlan = self.create_vlan()
        self.get_vlan_attribute(vlan)
        self.set_vlan_attribute(vlan)
        self.get_vlan_stats(vlan)
        self.remove_vlan(vlan)

    def create_vlan(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_VLAN_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_VLAN_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["vlan_id"] = 100
        vlan = sai_thrift_create_vlan(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return vlan

    def get_vlan_attribute(self, vlan):
        verify_object_attributes(self, sai_thrift_get_vlan_attribute, vlan, "SAI_VLAN_ATTR_")

    def set_vlan_attribute(self, vlan):
        status = sai_thrift_set_vlan_attribute(self.client, vlan, learn_disable=False)
        self._assert_status_success(status)

    def get_vlan_stats(self, vlan):
        counter_ids = sai_thrift_s32_list_t(count=1, int32list=[SAI_VLAN_STAT_IN_OCTETS])
        sai_thrift_get_vlan_stats(self.client, vlan, counter_ids)
        self._assert_status_success(adapter.status)

    def remove_vlan(self, vlan):
        status = sai_thrift_remove_vlan(self.client, vlan)
        self._assert_status_success(status)


class TestVlanMemberCrud(_AssertMixin, ThriftInterface):
    """
    VLAN Member mandatory attrs:
      SAI_VLAN_MEMBER_ATTR_VLAN_ID        (OID, no default)
      SAI_VLAN_MEMBER_ATTR_BRIDGE_PORT_ID (OID, no default)
    """

    def runTest(self):
        vlan = sai_thrift_create_vlan(self.client, vlan_id=200)

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

        member = self.create_vlan_member(vlan, bridge_port)
        self.get_vlan_member_attribute(member)
        self.remove_vlan_member(member)

        sai_thrift_remove_bridge_port(self.client, bridge_port)
        sai_thrift_remove_vlan(self.client, vlan)

    def create_vlan_member(self, vlan, bridge_port):
        mandatory = get_mandatory_attrs_from_csv("SAI_VLAN_MEMBER_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_VLAN_MEMBER_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["vlan_id"] = vlan
        kwargs["bridge_port_id"] = bridge_port
        member = sai_thrift_create_vlan_member(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return member

    def get_vlan_member_attribute(self, member):
        verify_object_attributes(self, sai_thrift_get_vlan_member_attribute, member, "SAI_VLAN_MEMBER_ATTR_")

    def remove_vlan_member(self, member):
        status = sai_thrift_remove_vlan_member(self.client, member)
        self._assert_status_success(status)
