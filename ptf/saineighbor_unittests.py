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
SAI PTFv2 Unit Tests for Neighbor feature (saineighbor.h)
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
class TestNeighborEntryCrud(_AssertMixin, ThriftInterface):
    """
    Neighbor Entry uses a struct key (rif_id, ip_address), not an OID.
    Mandatory attrs from CSV:
      SAI_NEIGHBOR_ENTRY_ATTR_DST_MAC_ADDRESS (mac, no default – use test value)
    Prerequisites: virtual router, router interface.
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

        neighbor_entry = sai_thrift_neighbor_entry_t(
            rif_id=rif,
            ip_address=sai_thrift_ip_address_t(
                addr_family=SAI_IP_ADDR_FAMILY_IPV4,
                addr=sai_thrift_ip_addr_t(ip4="10.0.0.1"),
            ),
        )

        self.create_neighbor_entry(neighbor_entry)
        self.get_neighbor_entry_attribute(neighbor_entry)
        self.set_neighbor_entry_attribute(neighbor_entry)
        self.remove_neighbor_entry(neighbor_entry)

        sai_thrift_remove_router_interface(self.client, rif)
        sai_thrift_remove_virtual_router(self.client, vr)

    def create_neighbor_entry(self, neighbor_entry):
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_NEIGHBOR_ENTRY_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_NEIGHBOR_ENTRY_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # dst_mac_address has no CSV default – supply a test value.
        kwargs["dst_mac_address"] = "00:11:22:33:44:55"
        status = sai_thrift_create_neighbor_entry(
            self.client, neighbor_entry, **kwargs
        )
        self._assert_status_success(status)

    def get_neighbor_entry_attribute(self, neighbor_entry):
        verify_object_attributes(
            self, sai_thrift_get_neighbor_entry_attribute,
            neighbor_entry, "SAI_NEIGHBOR_ENTRY_ATTR_",
        )

    def set_neighbor_entry_attribute(self, neighbor_entry):
        status = sai_thrift_set_neighbor_entry_attribute(
            self.client, neighbor_entry, no_host_route=False
        )
        self._assert_status_success(status)

    def remove_neighbor_entry(self, neighbor_entry):
        status = sai_thrift_remove_neighbor_entry(self.client, neighbor_entry)
        self._assert_status_success(status)
