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

"""SAI PTFv2 Unit Tests for Debug Counter feature (saidebugcounter.h)"""

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


class TestDebugCounterCrud(_AssertMixin, ThriftInterface):
    """
import os as _os
import sys as _sys
# Add ptf/ to sys.path so sai_base_test and sai_utils can be found when
# this file is run from ptf/unittests/.
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))


    Debug Counter mandatory attrs from CSV:
      SAI_DEBUG_COUNTER_ATTR_TYPE (default: SAI_DEBUG_COUNTER_TYPE_PORT_IN_DROP_REASONS)
    """

    def runTest(self):
        counter = self.create_debug_counter()
        self.get_debug_counter_attribute(counter)
        self.set_debug_counter_attribute(counter)
        self.remove_debug_counter(counter)

    def create_debug_counter(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_DEBUG_COUNTER_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_DEBUG_COUNTER_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        counter = sai_thrift_create_debug_counter(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return counter

    def get_debug_counter_attribute(self, counter):
        verify_object_attributes(self, sai_thrift_get_debug_counter_attribute, counter, "SAI_DEBUG_COUNTER_ATTR_")

    def set_debug_counter_attribute(self, counter):
        drop_reasons = sai_thrift_s32_list_t(count=0, int32list=[])
        status = sai_thrift_set_debug_counter_attribute(
            self.client, counter, in_drop_reason_list=drop_reasons
        )
        self._assert_status_success(status)

    def remove_debug_counter(self, counter):
        status = sai_thrift_remove_debug_counter(self.client, counter)
        self._assert_status_success(status)
