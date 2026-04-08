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
SAI PTFv2 Unit Tests for Next Hop Group feature (sainexthopgroup.h)
"""

from sai_base_test import ThriftInterface
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter
import sai_thrift.sai_headers as sai_headers

from sai_utils import (
    get_mandatory_attrs_from_csv,
    verify_object_attributes,
    load_attr_defaults,
)

_ATTR_DEFAULTS = load_attr_defaults()


class _AssertMixin:
    def _assert_status_success(self, status, msg=""):
        self.assertEqual(status, SAI_STATUS_SUCCESS,
                         msg or "Expected SAI_STATUS_SUCCESS, got {}".format(status))
class TestNextHopGroupCrud(_AssertMixin, ThriftInterface):
    """
    Next Hop Group mandatory attrs from CSV:
      SAI_NEXT_HOP_GROUP_ATTR_TYPE (default: SAI_NEXT_HOP_GROUP_TYPE_DYNAMIC_UNORDERED_ECMP)
    """

    def runTest(self):
        nhg = self.create_next_hop_group()
        self.get_next_hop_group_attribute(nhg)
        self.set_next_hop_group_attribute(nhg)
        self.remove_next_hop_group(nhg)

    def create_next_hop_group(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_NEXT_HOP_GROUP_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_NEXT_HOP_GROUP_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        nhg = sai_thrift_create_next_hop_group(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return nhg

    def get_next_hop_group_attribute(self, nhg):
        verify_object_attributes(
            self, sai_thrift_get_next_hop_group_attribute,
            nhg, "SAI_NEXT_HOP_GROUP_ATTR_",
        )

    def set_next_hop_group_attribute(self, nhg):
        status = sai_thrift_set_next_hop_group_attribute(
            self.client, nhg, set_switchover=False
        )
        self._assert_status_success(status)

    def remove_next_hop_group(self, nhg):
        status = sai_thrift_remove_next_hop_group(self.client, nhg)
        self._assert_status_success(status)


class TestNextHopGroupMemberCrud(_AssertMixin, ThriftInterface):
    """
    Next Hop Group Member mandatory attrs from CSV:
      SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_GROUP_ID (OID, no default)
      SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_ID       (OID, no default)
    Prerequisites: virtual router, router interface, next hop, next hop group.
    """

    def runTest(self):
        vr = sai_thrift_create_virtual_router(self.client)

        attr = sai_thrift_get_switch_attribute(
            self.client, number_of_active_ports=True
        )
        num_ports = attr["number_of_active_ports"]
        attr = sai_thrift_get_switch_attribute(
            self.client,
            port_list=sai_thrift_object_list_t(idlist=[], count=num_ports),
        )
        port_id = attr["port_list"].idlist[0]

        rif = sai_thrift_create_router_interface(
            self.client,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            virtual_router_id=vr,
            port_id=port_id,
        )

        nh = sai_thrift_create_next_hop(
            self.client,
            type=SAI_NEXT_HOP_TYPE_IP,
            ip=sai_thrift_ip_address_t(
                addr_family=SAI_IP_ADDR_FAMILY_IPV4,
                addr=sai_thrift_ip_addr_t(ip4="10.0.0.1"),
            ),
            router_interface_id=rif,
        )

        nhg_kwargs = {
            attr[len("SAI_NEXT_HOP_GROUP_ATTR_"):].lower():
                getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv(
                "SAI_NEXT_HOP_GROUP_ATTR_", _ATTR_DEFAULTS)
            for _, default, _ in [_ATTR_DEFAULTS[attr]] if default
        }
        nhg = sai_thrift_create_next_hop_group(self.client, **nhg_kwargs)

        member = self.create_next_hop_group_member(nhg, nh)
        self.get_next_hop_group_member_attribute(member)
        self.set_next_hop_group_member_attribute(member)
        self.remove_next_hop_group_member(member)

        sai_thrift_remove_next_hop_group(self.client, nhg)
        sai_thrift_remove_next_hop(self.client, nh)
        sai_thrift_remove_router_interface(self.client, rif)
        sai_thrift_remove_virtual_router(self.client, vr)

    def create_next_hop_group_member(self, nhg, nh):
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_NEXT_HOP_GROUP_MEMBER_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_NEXT_HOP_GROUP_MEMBER_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["next_hop_group_id"] = nhg
        kwargs["next_hop_id"] = nh
        member = sai_thrift_create_next_hop_group_member(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return member

    def get_next_hop_group_member_attribute(self, member):
        verify_object_attributes(
            self, sai_thrift_get_next_hop_group_member_attribute,
            member, "SAI_NEXT_HOP_GROUP_MEMBER_ATTR_",
        )

    def set_next_hop_group_member_attribute(self, member):
        status = sai_thrift_set_next_hop_group_member_attribute(
            self.client, member, weight=1
        )
        self._assert_status_success(status)

    def remove_next_hop_group_member(self, member):
        status = sai_thrift_remove_next_hop_group_member(self.client, member)
        self._assert_status_success(status)
