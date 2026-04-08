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
SAI PTFv2 Unit Tests for Host Interface feature (saihostif.h)
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


class TestHostifApiDiscovery(ThriftInterface):
    EXPECTED_FUNCTIONS = [
        "sai_thrift_create_hostif",
        "sai_thrift_remove_hostif",
        "sai_thrift_set_hostif_attribute",
        "sai_thrift_get_hostif_attribute",
        "sai_thrift_create_hostif_trap_group",
        "sai_thrift_remove_hostif_trap_group",
        "sai_thrift_set_hostif_trap_group_attribute",
        "sai_thrift_get_hostif_trap_group_attribute",
        "sai_thrift_create_hostif_trap",
        "sai_thrift_remove_hostif_trap",
        "sai_thrift_set_hostif_trap_attribute",
        "sai_thrift_get_hostif_trap_attribute",
    ]
    EXPECTED_ATTR_PREFIXES = [
        "SAI_HOSTIF_ATTR_",
        "SAI_HOSTIF_TRAP_GROUP_ATTR_",
        "SAI_HOSTIF_TRAP_ATTR_",
    ]

    def runTest(self):
        discovered = {n for n, _ in get_sai_api_functions("_hostif")}
        for fn in self.EXPECTED_FUNCTIONS:
            self.assertIn(fn, discovered)
        constants = get_sai_attribute_constants(sai_headers, *self.EXPECTED_ATTR_PREFIXES)
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            self.assertTrue(any(k.startswith(prefix) for k in constants))


class TestHostifTrapGroupCrud(_AssertMixin, ThriftInterface):
    """Hostif Trap Group has no mandatory attrs; create with all defaults."""

    def runTest(self):
        trap_group = self.create_hostif_trap_group()
        self.get_hostif_trap_group_attribute(trap_group)
        self.set_hostif_trap_group_attribute(trap_group)
        self.remove_hostif_trap_group(trap_group)

    def create_hostif_trap_group(self):
        trap_group = sai_thrift_create_hostif_trap_group(self.client)
        self._assert_status_success(adapter.status)
        return trap_group

    def get_hostif_trap_group_attribute(self, trap_group):
        verify_object_attributes(
            self, sai_thrift_get_hostif_trap_group_attribute,
            trap_group, "SAI_HOSTIF_TRAP_GROUP_ATTR_",
        )

    def set_hostif_trap_group_attribute(self, trap_group):
        status = sai_thrift_set_hostif_trap_group_attribute(
            self.client, trap_group, admin_state=True
        )
        self._assert_status_success(status)

    def remove_hostif_trap_group(self, trap_group):
        status = sai_thrift_remove_hostif_trap_group(self.client, trap_group)
        self._assert_status_success(status)


class TestHostifTrapCrud(_AssertMixin, ThriftInterface):
    """
    Hostif Trap mandatory attrs from CSV:
      SAI_HOSTIF_TRAP_ATTR_TRAP_TYPE     (default: SAI_HOSTIF_TRAP_TYPE_START)
      SAI_HOSTIF_TRAP_ATTR_PACKET_ACTION (default: SAI_PACKET_ACTION_DROP)
    """

    def runTest(self):
        trap = self.create_hostif_trap()
        self.get_hostif_trap_attribute(trap)
        self.set_hostif_trap_attribute(trap)
        self.remove_hostif_trap(trap)

    def create_hostif_trap(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_HOSTIF_TRAP_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_HOSTIF_TRAP_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        trap = sai_thrift_create_hostif_trap(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return trap

    def get_hostif_trap_attribute(self, trap):
        verify_object_attributes(
            self, sai_thrift_get_hostif_trap_attribute,
            trap, "SAI_HOSTIF_TRAP_ATTR_",
        )

    def set_hostif_trap_attribute(self, trap):
        status = sai_thrift_set_hostif_trap_attribute(
            self.client, trap, packet_action=SAI_PACKET_ACTION_DROP
        )
        self._assert_status_success(status)

    def remove_hostif_trap(self, trap):
        status = sai_thrift_remove_hostif_trap(self.client, trap)
        self._assert_status_success(status)


class TestHostifCrud(_AssertMixin, ThriftInterface):
    """
    Hostif mandatory attrs from CSV:
      SAI_HOSTIF_ATTR_TYPE   (default: SAI_HOSTIF_TYPE_NETDEV)
      SAI_HOSTIF_ATTR_NAME   (char, no default – use 'test_hif')
      SAI_HOSTIF_ATTR_OBJ_ID (OID, no default – use first active port)
    """

    def runTest(self):
        attr = sai_thrift_get_switch_attribute(
            self.client, number_of_active_ports=True
        )
        num_ports = attr["number_of_active_ports"]
        attr = sai_thrift_get_switch_attribute(
            self.client,
            port_list=sai_thrift_object_list_t(idlist=[], count=num_ports),
        )
        port_id = attr["port_list"].idlist[0]

        hif = self.create_hostif(port_id)
        self.get_hostif_attribute(hif)
        self.set_hostif_attribute(hif)
        self.remove_hostif(hif)

    def create_hostif(self, port_id):
        mandatory = get_mandatory_attrs_from_csv("SAI_HOSTIF_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_HOSTIF_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["obj_id"] = port_id
        kwargs["name"] = "test_hif"
        hif = sai_thrift_create_hostif(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return hif

    def get_hostif_attribute(self, hif):
        verify_object_attributes(
            self, sai_thrift_get_hostif_attribute, hif, "SAI_HOSTIF_ATTR_",
        )

    def set_hostif_attribute(self, hif):
        status = sai_thrift_set_hostif_attribute(
            self.client, hif, oper_status=True
        )
        self._assert_status_success(status)

    def remove_hostif(self, hif):
        status = sai_thrift_remove_hostif(self.client, hif)
        self._assert_status_success(status)
