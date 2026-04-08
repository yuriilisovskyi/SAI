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
SAI PTFv2 Unit Tests for Next Hop feature (sainexthop.h)
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


class TestNextHopApiDiscovery(ThriftInterface):
    EXPECTED_FUNCTIONS = [
        "sai_thrift_create_next_hop",
        "sai_thrift_remove_next_hop",
        "sai_thrift_set_next_hop_attribute",
        "sai_thrift_get_next_hop_attribute",
    ]
    EXPECTED_ATTR_PREFIXES = ["SAI_NEXT_HOP_ATTR_"]

    def runTest(self):
        discovered = {n for n, _ in get_sai_api_functions("_next_hop")}
        for fn in self.EXPECTED_FUNCTIONS:
            self.assertIn(fn, discovered)
        constants = get_sai_attribute_constants(sai_headers, *self.EXPECTED_ATTR_PREFIXES)
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            self.assertTrue(any(k.startswith(prefix) for k in constants))


class TestNextHopCrud(_AssertMixin, ThriftInterface):
    """
    Next Hop mandatory attrs from CSV:
      SAI_NEXT_HOP_ATTR_TYPE                 (default: SAI_NEXT_HOP_TYPE_IP)
      SAI_NEXT_HOP_ATTR_IP                   (ip_address, no default)
      SAI_NEXT_HOP_ATTR_ROUTER_INTERFACE_ID  (OID, conditional on TYPE=IP, no default)
      SAI_NEXT_HOP_ATTR_TUNNEL_ID            (OID, conditional on TYPE=TUNNEL)
      SAI_NEXT_HOP_ATTR_SRV6_SIDLIST_ID      (OID, conditional on TYPE=SRV6_SIDLIST)
      SAI_NEXT_HOP_ATTR_LABELSTACK           (list, conditional on TYPE=MPLS)
    For default TYPE=SAI_NEXT_HOP_TYPE_IP: TYPE + IP + ROUTER_INTERFACE_ID are needed.
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

        nh = self.create_next_hop(rif)
        self.get_next_hop_attribute(nh)
        self.set_next_hop_attribute(nh)
        self.remove_next_hop(nh)

        sai_thrift_remove_router_interface(self.client, rif)
        sai_thrift_remove_virtual_router(self.client, vr)

    def create_next_hop(self, rif):
        mandatory = get_mandatory_attrs_from_csv("SAI_NEXT_HOP_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_NEXT_HOP_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # Supply runtime values for TYPE=IP mandatory attrs without CSV defaults.
        kwargs["type"] = SAI_NEXT_HOP_TYPE_IP
        kwargs["ip"] = sai_thrift_ip_address_t(
            addr_family=SAI_IP_ADDR_FAMILY_IPV4,
            addr=sai_thrift_ip_addr_t(ip4="10.0.0.1"),
        )
        kwargs["router_interface_id"] = rif
        nh = sai_thrift_create_next_hop(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return nh

    def get_next_hop_attribute(self, nh):
        verify_object_attributes(
            self, sai_thrift_get_next_hop_attribute, nh, "SAI_NEXT_HOP_ATTR_",
        )

    def set_next_hop_attribute(self, nh):
        status = sai_thrift_set_next_hop_attribute(
            self.client, nh, disable_decrement_ttl=False
        )
        self._assert_status_success(status)

    def remove_next_hop(self, nh):
        status = sai_thrift_remove_next_hop(self.client, nh)
        self._assert_status_success(status)
