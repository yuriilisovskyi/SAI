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
SAI PTFv2 Unit Tests for Switch feature (saiswitch.h)

Note: Switch create is handled by the PTFv2 framework's SaiHelperBase.setUp()
and should not be repeated in tests against a running switch.  These tests
validate the get and set APIs on the already-initialised switch, and verify
that all API functions and attribute constants are discoverable from sai_thrift.
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


class TestSwitchApiDiscovery(ThriftInterface):
    EXPECTED_FUNCTIONS = [
        "sai_thrift_create_switch",
        "sai_thrift_remove_switch",
        "sai_thrift_set_switch_attribute",
        "sai_thrift_get_switch_attribute",
    ]
    EXPECTED_ATTR_PREFIXES = ["SAI_SWITCH_ATTR_"]

    def runTest(self):
        discovered = {n for n, _ in get_sai_api_functions("_switch")}
        for fn in self.EXPECTED_FUNCTIONS:
            self.assertIn(fn, discovered)
        constants = get_sai_attribute_constants(sai_headers, *self.EXPECTED_ATTR_PREFIXES)
        for prefix in self.EXPECTED_ATTR_PREFIXES:
            self.assertTrue(any(k.startswith(prefix) for k in constants))


class TestSwitchGetSetAttribute(_AssertMixin, ThriftInterface):
    """
    Validates get and set on the already-initialised switch object.
    The switch OID is obtained via sai_thrift_create_switch with
    init_switch=True (which returns the existing switch handle if already
    initialised, as used by all PTFv2 tests).
    get iterates all SAI_SWITCH_ATTR_* attributes from sai_attr_defaults.csv
    and validates each returned value against its defined default.
    """

    def runTest(self):
        switch_id = sai_thrift_create_switch(
            self.client,
            init_switch=True,
            src_mac_address="00:77:66:55:44:00",
        )
        self._assert_status_success(adapter.status)

        self.get_switch_attribute(switch_id)
        self.set_switch_attribute(switch_id)

    def get_switch_attribute(self, switch_id):
        verify_object_attributes(
            self, sai_thrift_get_switch_attribute,
            switch_id, "SAI_SWITCH_ATTR_",
        )

    def set_switch_attribute(self, switch_id):
        status = sai_thrift_set_switch_attribute(
            self.client, switch_id, fdb_aging_time=0
        )
        self._assert_status_success(status)
