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
SAI PTFv2 Unit Tests for Route feature (sairoute.h)
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

_ATTR_DEFAULTS = load_attr_defaults()


class _AssertMixin:
    def _assert_status_success(self, status, msg=""):
        self.assertEqual(status, SAI_STATUS_SUCCESS,
                         msg or "Expected SAI_STATUS_SUCCESS, got {}".format(status))


class TestRouteApiDiscovery(ThriftInterface):
    EXPECTED_FUNCTIONS = [
        "sai_thrift_create_route_entry",
        "sai_thrift_remove_route_entry",
        "sai_thrift_set_route_entry_attribute",
        "sai_thrift_get_route_entry_attribute",
    ]
    EXPECTED_ATTR_PREFIXES = ["SAI_ROUTE_ENTRY_ATTR_"]

    def runTest(self):
        discovered = {n for n, _ in get_sai_api_functions("_route")}
        for fn in self.EXPECTED_FUNCTIONS:
            self.assertIn(fn, discovered)
        constants = get_sai_attribute_constants(sai_headers, *self.EXPECTED_ATTR_PREFIXES)
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            self.assertTrue(any(k.startswith(prefix) for k in constants))


class TestRouteEntryCrud(_AssertMixin, ThriftInterface):
    """
    Route Entry uses a struct key (vr_id, destination).
    No mandatory attrs from CSV (all are optional with defaults).
    Prerequisites: virtual router, router interface, next hop.
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

        route_entry = sai_thrift_route_entry_t(
            vr_id=vr,
            destination=sai_thrift_ip_prefix_t(
                addr_family=SAI_IP_ADDR_FAMILY_IPV4,
                addr=sai_thrift_ip_addr_t(ip4="192.168.1.0"),
                mask=sai_thrift_ip_addr_t(ip4="255.255.255.0"),
            ),
        )

        self.create_route_entry(route_entry, nh)
        self.get_route_entry_attribute(route_entry)
        self.set_route_entry_attribute(route_entry)
        self.remove_route_entry(route_entry)

        sai_thrift_remove_next_hop(self.client, nh)
        sai_thrift_remove_router_interface(self.client, rif)
        sai_thrift_remove_virtual_router(self.client, vr)

    def create_route_entry(self, route_entry, nh):
        # No mandatory attrs from CSV; supply next_hop_id as it's needed
        # to create a useful route (otherwise packet_action default=DROP is used).
        status = sai_thrift_create_route_entry(
            self.client, route_entry, next_hop_id=nh
        )
        self._assert_status_success(status)

    def get_route_entry_attribute(self, route_entry):
        verify_object_attributes(
            self, sai_thrift_get_route_entry_attribute,
            route_entry, "SAI_ROUTE_ENTRY_ATTR_",
        )

    def set_route_entry_attribute(self, route_entry):
        status = sai_thrift_set_route_entry_attribute(
            self.client, route_entry, packet_action=SAI_PACKET_ACTION_FORWARD
        )
        self._assert_status_success(status)

    def remove_route_entry(self, route_entry):
        status = sai_thrift_remove_route_entry(self.client, route_entry)
        self._assert_status_success(status)
