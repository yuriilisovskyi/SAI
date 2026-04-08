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
SAI PTFv2 Unit Tests for Router Interface feature (sairouterinterface.h)
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
class TestRouterInterfaceCrud(_AssertMixin, ThriftInterface):
    """
    Router Interface mandatory attrs from CSV:
      SAI_ROUTER_INTERFACE_ATTR_TYPE               (default: SAI_ROUTER_INTERFACE_TYPE_PORT)
      SAI_ROUTER_INTERFACE_ATTR_VIRTUAL_ROUTER_ID  (OID, no default)
      SAI_ROUTER_INTERFACE_ATTR_PORT_ID            (OID, conditional on TYPE=PORT)
      SAI_ROUTER_INTERFACE_ATTR_VLAN_ID            (OID, conditional on TYPE=VLAN)
      SAI_ROUTER_INTERFACE_ATTR_BRIDGE_ID          (OID, conditional on TYPE=BRIDGE)
      SAI_ROUTER_INTERFACE_ATTR_OUTER_VLAN_ID      (uint16, conditional on TYPE=QINQ)
      SAI_ROUTER_INTERFACE_ATTR_INNER_VLAN_ID      (uint16, conditional on TYPE=QINQ)
    For default TYPE=SAI_ROUTER_INTERFACE_TYPE_PORT: TYPE + VIRTUAL_ROUTER_ID + PORT_ID.
    Prerequisites: virtual router, first active port.
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

        rif = self.create_router_interface(vr, port_id)
        self.get_router_interface_attribute(rif)
        self.set_router_interface_attribute(rif)
        self.remove_router_interface(rif)

        sai_thrift_remove_virtual_router(self.client, vr)

    def create_router_interface(self, vr, port_id):
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_ROUTER_INTERFACE_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_ROUTER_INTERFACE_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # Supply runtime OID values for mandatory attrs without CSV defaults.
        kwargs["type"] = SAI_ROUTER_INTERFACE_TYPE_PORT
        kwargs["virtual_router_id"] = vr
        kwargs["port_id"] = port_id
        rif = sai_thrift_create_router_interface(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return rif

    def get_router_interface_attribute(self, rif):
        verify_object_attributes(
            self, sai_thrift_get_router_interface_attribute,
            rif, "SAI_ROUTER_INTERFACE_ATTR_",
        )

    def set_router_interface_attribute(self, rif):
        status = sai_thrift_set_router_interface_attribute(
            self.client, rif, admin_v4_state=True
        )
        self._assert_status_success(status)

    def remove_router_interface(self, rif):
        status = sai_thrift_remove_router_interface(self.client, rif)
        self._assert_status_success(status)
