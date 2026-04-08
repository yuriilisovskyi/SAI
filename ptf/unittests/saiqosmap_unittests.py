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

"""SAI PTFv2 Unit Tests for QoS Map feature (saiqosmap.h)"""

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


class TestQosMapCrud(_AssertMixin, ThriftInterface):
    """
import os as _os
import sys as _sys
# Add ptf/ to sys.path so sai_base_test and sai_utils can be found when
# this file is run from ptf/unittests/.
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))


    QoS Map mandatory attrs from CSV:
      SAI_QOS_MAP_ATTR_TYPE              (default: SAI_QOS_MAP_TYPE_DOT1P_TO_TC)
      SAI_QOS_MAP_ATTR_MAP_TO_VALUE_LIST (sai_qos_map_list_t, no default – empty list)
    """

    def runTest(self):
        qos_map = self.create_qos_map()
        self.get_qos_map_attribute(qos_map)
        self.remove_qos_map(qos_map)

    def create_qos_map(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_QOS_MAP_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_QOS_MAP_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["map_to_value_list"] = sai_thrift_qos_map_list_t(count=0, maplist=[])
        qos_map = sai_thrift_create_qos_map(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return qos_map

    def get_qos_map_attribute(self, qos_map):
        verify_object_attributes(self, sai_thrift_get_qos_map_attribute, qos_map, "SAI_QOS_MAP_ATTR_")

    def remove_qos_map(self, qos_map):
        status = sai_thrift_remove_qos_map(self.client, qos_map)
        self._assert_status_success(status)
