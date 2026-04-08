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
SAI PTFv2 Unit Tests for Port feature (saiport.h)
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


class TestPortApiDiscovery(ThriftInterface):
    EXPECTED_FUNCTIONS = [
        "sai_thrift_create_port",
        "sai_thrift_remove_port",
        "sai_thrift_set_port_attribute",
        "sai_thrift_get_port_attribute",
    ]
    EXPECTED_ATTR_PREFIXES = ["SAI_PORT_ATTR_"]

    def runTest(self):
        discovered = {n for n, _ in get_sai_api_functions("_port")}
        for fn in self.EXPECTED_FUNCTIONS:
            self.assertIn(fn, discovered)
        constants = get_sai_attribute_constants(sai_headers, *self.EXPECTED_ATTR_PREFIXES)
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            self.assertTrue(any(k.startswith(prefix) for k in constants))


class TestPortCrud(_AssertMixin, ThriftInterface):
    """
    Port mandatory attrs from CSV:
      SAI_PORT_ATTR_HW_LANE_LIST (sai_u32_list_t, no default)
      SAI_PORT_ATTR_SPEED        (uint32, no default)

    Uses the first active port's existing lane list and speed so the test
    works without knowing real hardware lanes. The port is removed and
    re-created with the same attributes.
    """

    def runTest(self):
        # Get an existing port to read its HW lane list and speed.
        attr = sai_thrift_get_switch_attribute(
            self.client, number_of_active_ports=True
        )
        num_ports = attr["number_of_active_ports"]
        attr = sai_thrift_get_switch_attribute(
            self.client,
            port_list=sai_thrift_object_list_t(idlist=[], count=num_ports),
        )
        existing_port_id = attr["port_list"].idlist[0]

        port_attrs = sai_thrift_get_port_attribute(
            self.client,
            existing_port_id,
            hw_lane_list=sai_thrift_u32_list_t(count=8, uint32list=[]),
            speed=True,
        )
        hw_lane_list = port_attrs["hw_lane_list"]
        speed = port_attrs["speed"]

        # Remove the existing port and re-create with the same parameters.
        sai_thrift_remove_port(self.client, existing_port_id)

        port = self.create_port(hw_lane_list, speed)
        self.get_port_attribute(port)
        self.set_port_attribute(port)
        self.remove_port(port)

    def create_port(self, hw_lane_list, speed):
        mandatory = get_mandatory_attrs_from_csv("SAI_PORT_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_PORT_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["hw_lane_list"] = hw_lane_list
        kwargs["speed"] = speed
        port = sai_thrift_create_port(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return port

    def get_port_attribute(self, port):
        verify_object_attributes(
            self, sai_thrift_get_port_attribute, port, "SAI_PORT_ATTR_",
        )

    def set_port_attribute(self, port):
        status = sai_thrift_set_port_attribute(
            self.client, port, admin_state=True
        )
        self._assert_status_success(status)

    def remove_port(self, port):
        status = sai_thrift_remove_port(self.client, port)
        self._assert_status_success(status)
