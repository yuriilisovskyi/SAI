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
SAI PTFv2 Unit Tests for Tunnel feature (saitunnel.h)
"""

from sai_base_test import ThriftInterface
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter
import sai_thrift.sai_headers as sai_headers

from sai_utils import (
    get_mandatory_on_create_attrs,
    get_mandatory_attrs_from_csv,
    get_non_crud_apis,
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


class TestTunnelApiDiscovery(ThriftInterface):
    SAI_OBJECT_TYPES = [
        "SAI_OBJECT_TYPE_TUNNEL",
        "SAI_OBJECT_TYPE_TUNNEL_MAP",
        "SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY",
        "SAI_OBJECT_TYPE_TUNNEL_TERM_TABLE_ENTRY"
    ]

    EXPECTED_FUNCTIONS = [
        "sai_thrift_create_tunnel",
        "sai_thrift_remove_tunnel",
        "sai_thrift_set_tunnel_attribute",
        "sai_thrift_get_tunnel_attribute",
        "sai_thrift_create_tunnel_map",
        "sai_thrift_remove_tunnel_map",
        "sai_thrift_set_tunnel_map_attribute",
        "sai_thrift_get_tunnel_map_attribute",
        "sai_thrift_create_tunnel_map_entry",
        "sai_thrift_remove_tunnel_map_entry",
        "sai_thrift_set_tunnel_map_entry_attribute",
        "sai_thrift_get_tunnel_map_entry_attribute",
        "sai_thrift_create_tunnel_term_table_entry",
        "sai_thrift_remove_tunnel_term_table_entry",
        "sai_thrift_set_tunnel_term_table_entry_attribute",
        "sai_thrift_get_tunnel_term_table_entry_attribute",
    ]
    EXPECTED_ATTR_PREFIXES = [
        "SAI_TUNNEL_ATTR_",
        "SAI_TUNNEL_MAP_ATTR_",
        "SAI_TUNNEL_MAP_ENTRY_ATTR_",
        "SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_",
    ]

    def runTest(self):
        discovered = {n for n, _ in get_sai_api_functions("_tunnel")}
        for fn in self.EXPECTED_FUNCTIONS:
            self.verify_non_crud_apis()
        self.assertIn(fn, discovered)
        constants = get_sai_attribute_constants(sai_headers, *self.EXPECTED_ATTR_PREFIXES)
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            self.assertTrue(any(k.startswith(prefix) for k in constants))


    def verify_non_crud_apis(self):
        """Non-CRUD APIs for this object are callable from sai_thrift.sai_adapter."""
        import sai_thrift.sai_adapter as _adapter
        for obj_type in self.SAI_OBJECT_TYPES:
            for fn_name in get_non_crud_apis(obj_type):
                self.assertTrue(
                    hasattr(_adapter, fn_name),
                    "Non-CRUD function '{}' not found in sai_thrift.sai_adapter".format(fn_name),
                )

class TestTunnelMapCrud(_AssertMixin, ThriftInterface):
    """
    Tunnel Map mandatory attrs from CSV:
      SAI_TUNNEL_MAP_ATTR_TYPE (default: SAI_TUNNEL_MAP_TYPE_OECN_TO_UECN)
    """

    def runTest(self):
        tmap = self.create_tunnel_map()
        self.get_tunnel_map_attribute(tmap)
        self.remove_tunnel_map(tmap)

    def create_tunnel_map(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_TUNNEL_MAP_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_TUNNEL_MAP_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        tmap = sai_thrift_create_tunnel_map(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return tmap

    def get_tunnel_map_attribute(self, tmap):
        verify_object_attributes(
            self, sai_thrift_get_tunnel_map_attribute, tmap, "SAI_TUNNEL_MAP_ATTR_",
        )

    def remove_tunnel_map(self, tmap):
        status = sai_thrift_remove_tunnel_map(self.client, tmap)
        self._assert_status_success(status)


class TestTunnelCrud(_AssertMixin, ThriftInterface):
    """
    Tunnel mandatory attrs from CSV:
      SAI_TUNNEL_ATTR_TYPE               (default: SAI_TUNNEL_TYPE_IPINIP)
      SAI_TUNNEL_ATTR_OVERLAY_INTERFACE  (OID, no default)
      SAI_TUNNEL_ATTR_UNDERLAY_INTERFACE (OID, no default)
    Prerequisites: virtual router and two router interfaces (overlay/underlay).
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
        port_ids = attr["port_list"].idlist

        overlay_rif = sai_thrift_create_router_interface(
            self.client,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            virtual_router_id=vr,
            port_id=port_ids[0],
        )
        underlay_rif = sai_thrift_create_router_interface(
            self.client,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            virtual_router_id=vr,
            port_id=port_ids[1] if len(port_ids) > 1 else port_ids[0],
        )

        tunnel = self.create_tunnel(overlay_rif, underlay_rif)
        self.get_tunnel_attribute(tunnel)
        self.set_tunnel_attribute(tunnel)
        self.remove_tunnel(tunnel)

        sai_thrift_remove_router_interface(self.client, underlay_rif)
        sai_thrift_remove_router_interface(self.client, overlay_rif)
        sai_thrift_remove_virtual_router(self.client, vr)

    def create_tunnel(self, overlay_rif, underlay_rif):
        mandatory = get_mandatory_attrs_from_csv("SAI_TUNNEL_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_TUNNEL_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["overlay_interface"] = overlay_rif
        kwargs["underlay_interface"] = underlay_rif
        tunnel = sai_thrift_create_tunnel(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return tunnel

    def get_tunnel_attribute(self, tunnel):
        verify_object_attributes(
            self, sai_thrift_get_tunnel_attribute, tunnel, "SAI_TUNNEL_ATTR_",
        )

    def set_tunnel_attribute(self, tunnel):
        status = sai_thrift_set_tunnel_attribute(
            self.client, tunnel, ttl_mode=SAI_TUNNEL_TTL_MODE_UNIFORM_MODEL
        )
        self._assert_status_success(status)

    def remove_tunnel(self, tunnel):
        status = sai_thrift_remove_tunnel(self.client, tunnel)
        self._assert_status_success(status)
