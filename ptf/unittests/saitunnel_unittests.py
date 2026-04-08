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

import os as _os
import sys as _sys
# Add ptf/ to sys.path so sai_base_test and sai_utils can be found when
# this file is run from ptf/unittests/.
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))


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


class TestTunnelNonCrudApis(_AssertMixin, ThriftInterface):
    """
    Validates non-CRUD Tunnel APIs from saitunnel.h:
      sai_thrift_get_tunnel_stats     – get tunnel counters
      sai_thrift_get_tunnel_stats_ext – get tunnel counters (extended mode)
      sai_thrift_clear_tunnel_stats   – clear tunnel counters
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

        tun_kwargs = {
            attr[len("SAI_TUNNEL_ATTR_"):].lower():
                getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv("SAI_TUNNEL_ATTR_", _ATTR_DEFAULTS)
            for _, default, _ in [_ATTR_DEFAULTS[attr]] if default
        }
        tun_kwargs["overlay_interface"] = overlay_rif
        tun_kwargs["underlay_interface"] = underlay_rif
        tunnel = sai_thrift_create_tunnel(self.client, **tun_kwargs)
        self._assert_status_success(adapter.status)
        counter_ids = sai_thrift_s32_list_t(
            count=1, int32list=[SAI_TUNNEL_STAT_IN_OCTETS]
        )

        sai_thrift_get_tunnel_stats(self.client, tunnel, counter_ids)
        self._assert_status_success(adapter.status)

        sai_thrift_get_tunnel_stats_ext(
            self.client, tunnel, SAI_STATS_MODE_READ, counter_ids
        )
        self._assert_status_success(adapter.status)

        status = sai_thrift_clear_tunnel_stats(self.client, tunnel, counter_ids)
        self._assert_status_success(status)

        sai_thrift_remove_tunnel(self.client, tunnel)
        sai_thrift_remove_router_interface(self.client, underlay_rif)
        sai_thrift_remove_router_interface(self.client, overlay_rif)
        sai_thrift_remove_virtual_router(self.client, vr)


class TestTunnelTermTableEntryCrud(_AssertMixin, ThriftInterface):
    """
    Tunnel Term Table Entry mandatory attrs from CSV:
      SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_VR_ID          (OID, no default)
      SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_TYPE            (default: SAI_TUNNEL_TERM_TABLE_ENTRY_TYPE_P2P)
      SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_DST_IP          (ip_address, no default)
      SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_SRC_IP          (ip_address, conditional on P2P)
      SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_TUNNEL_TYPE     (default: SAI_TUNNEL_TYPE_IPINIP)
      SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_ACTION_TUNNEL_ID (OID, no default)
    """

    def runTest(self):
        vr = sai_thrift_create_virtual_router(self.client)
        attr = sai_thrift_get_switch_attribute(self.client, number_of_active_ports=True)
        num_ports = attr["number_of_active_ports"]
        attr = sai_thrift_get_switch_attribute(
            self.client, port_list=sai_thrift_object_list_t(idlist=[], count=num_ports))
        port_ids = attr["port_list"].idlist

        overlay_rif = sai_thrift_create_router_interface(
            self.client, type=SAI_ROUTER_INTERFACE_TYPE_PORT, virtual_router_id=vr, port_id=port_ids[0])
        underlay_rif = sai_thrift_create_router_interface(
            self.client, type=SAI_ROUTER_INTERFACE_TYPE_PORT, virtual_router_id=vr,
            port_id=port_ids[1] if len(port_ids) > 1 else port_ids[0])

        tun_kwargs = {
            attr[len("SAI_TUNNEL_ATTR_"):].lower(): getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv("SAI_TUNNEL_ATTR_", _ATTR_DEFAULTS)
            for _, default, _ in [_ATTR_DEFAULTS[attr]] if default
        }
        tun_kwargs["overlay_interface"] = overlay_rif
        tun_kwargs["underlay_interface"] = underlay_rif
        tunnel = sai_thrift_create_tunnel(self.client, **tun_kwargs)

        term_entry = self.create_tunnel_term_table_entry(vr, tunnel)
        self.get_tunnel_term_table_entry_attribute(term_entry)
        self.remove_tunnel_term_table_entry(term_entry)

        sai_thrift_remove_tunnel(self.client, tunnel)
        sai_thrift_remove_router_interface(self.client, underlay_rif)
        sai_thrift_remove_router_interface(self.client, overlay_rif)
        sai_thrift_remove_virtual_router(self.client, vr)

    def create_tunnel_term_table_entry(self, vr, tunnel):
        mandatory = get_mandatory_attrs_from_csv("SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["vr_id"] = vr
        kwargs["action_tunnel_id"] = tunnel
        kwargs["dst_ip"] = sai_thrift_ip_address_t(
            addr_family=SAI_IP_ADDR_FAMILY_IPV4, addr=sai_thrift_ip_addr_t(ip4="192.168.1.1"))
        kwargs["src_ip"] = sai_thrift_ip_address_t(
            addr_family=SAI_IP_ADDR_FAMILY_IPV4, addr=sai_thrift_ip_addr_t(ip4="10.0.0.1"))
        term_entry = sai_thrift_create_tunnel_term_table_entry(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return term_entry

    def get_tunnel_term_table_entry_attribute(self, term_entry):
        verify_object_attributes(
            self, sai_thrift_get_tunnel_term_table_entry_attribute,
            term_entry, "SAI_TUNNEL_TERM_TABLE_ENTRY_ATTR_")

    def remove_tunnel_term_table_entry(self, term_entry):
        status = sai_thrift_remove_tunnel_term_table_entry(self.client, term_entry)
        self._assert_status_success(status)
