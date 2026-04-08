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

"""SAI PTFv2 Unit Tests for Policer feature (saipolicer.h)"""

from sai_base_test import ThriftInterface
from sai_thrift.sai_adapter import *  # noqa: F401,F403
from sai_thrift.sai_headers import *  # noqa: F401,F403
import sai_thrift.sai_adapter as adapter
import sai_thrift.sai_headers as sai_headers
from sai_utils import get_mandatory_attrs_from_csv, verify_object_attributes, load_attr_defaults

_ATTR_DEFAULTS = load_attr_defaults()


class _AssertMixin:
    def _assert_status_success(self, status, msg=""):
        self.assertEqual(status, SAI_STATUS_SUCCESS,
                         msg or "Expected SAI_STATUS_SUCCESS, got {}".format(status))


class TestPolicerCrud(_AssertMixin, ThriftInterface):
    """
    Policer mandatory attrs from CSV:
      SAI_POLICER_ATTR_METER_TYPE (default: SAI_METER_TYPE_PACKETS)
      SAI_POLICER_ATTR_MODE       (default: SAI_POLICER_MODE_SR_TCM)
    Non-CRUD: sai_thrift_get_policer_stats, sai_thrift_clear_policer_stats
    """

    def runTest(self):
        policer = self.create_policer()
        self.get_policer_attribute(policer)
        self.set_policer_attribute(policer)
        self.get_policer_stats(policer)
        self.clear_policer_stats(policer)
        self.remove_policer(policer)

    def create_policer(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_POLICER_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_POLICER_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        policer = sai_thrift_create_policer(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return policer

    def get_policer_attribute(self, policer):
        verify_object_attributes(self, sai_thrift_get_policer_attribute, policer, "SAI_POLICER_ATTR_")

    def set_policer_attribute(self, policer):
        status = sai_thrift_set_policer_attribute(
            self.client, policer, green_packet_action=SAI_PACKET_ACTION_FORWARD
        )
        self._assert_status_success(status)

    def get_policer_stats(self, policer):
        counter_ids = sai_thrift_s32_list_t(
            count=1, int32list=[SAI_POLICER_STAT_GREEN_PACKETS]
        )
        sai_thrift_get_policer_stats(self.client, policer, counter_ids)
        self._assert_status_success(adapter.status)

    def clear_policer_stats(self, policer):
        counter_ids = sai_thrift_s32_list_t(
            count=1, int32list=[SAI_POLICER_STAT_GREEN_PACKETS]
        )
        status = sai_thrift_clear_policer_stats(self.client, policer, counter_ids)
        self._assert_status_success(status)

    def remove_policer(self, policer):
        status = sai_thrift_remove_policer(self.client, policer)
        self._assert_status_success(status)
