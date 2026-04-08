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

"""SAI PTFv2 Unit Tests for Buffer feature (saibuffer.h)"""

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


class TestBufferPoolNonCrudApis(_AssertMixin, ThriftInterface):
    """
    Buffer Pool mandatory attrs from CSV:
      SAI_BUFFER_POOL_ATTR_TYPE (default: SAI_BUFFER_POOL_TYPE_INGRESS)
      SAI_BUFFER_POOL_ATTR_SIZE (uint64, no default – use 0 = unlimited)
    Non-CRUD: sai_thrift_get_buffer_pool_stats, sai_thrift_clear_buffer_pool_stats
    """

    def runTest(self):
        mandatory = get_mandatory_attrs_from_csv("SAI_BUFFER_POOL_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_BUFFER_POOL_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["size"] = 0
        pool = sai_thrift_create_buffer_pool(self.client, **kwargs)
        self._assert_status_success(adapter.status)

        verify_object_attributes(self, sai_thrift_get_buffer_pool_attribute, pool, "SAI_BUFFER_POOL_ATTR_")

        counter_ids = sai_thrift_s32_list_t(
            count=1, int32list=[SAI_BUFFER_POOL_STAT_CURR_OCCUPANCY_BYTES]
        )
        sai_thrift_get_buffer_pool_stats(self.client, pool, counter_ids)
        self._assert_status_success(adapter.status)

        status = sai_thrift_clear_buffer_pool_stats(self.client, pool, counter_ids)
        self._assert_status_success(status)

        sai_thrift_remove_buffer_pool(self.client, pool)


class TestBufferProfileCrud(_AssertMixin, ThriftInterface):
    """
    Buffer Profile mandatory attrs from CSV:
      SAI_BUFFER_PROFILE_ATTR_POOL_ID               (OID, no default)
      SAI_BUFFER_PROFILE_ATTR_RESERVED_BUFFER_SIZE  (uint64, no default – 0)
      SAI_BUFFER_PROFILE_ATTR_THRESHOLD_MODE        (default: SAI_BUFFER_PROFILE_THRESHOLD_MODE_STATIC)
      SAI_BUFFER_PROFILE_ATTR_SHARED_DYNAMIC_TH     (int8, conditional – omitted for STATIC mode)
      SAI_BUFFER_PROFILE_ATTR_SHARED_STATIC_TH      (uint64, conditional for STATIC mode – 0)
    """

    def runTest(self):
        pool_kwargs = {
            attr[len("SAI_BUFFER_POOL_ATTR_"):].lower(): getattr(sai_headers, default, default)
            for attr in get_mandatory_attrs_from_csv("SAI_BUFFER_POOL_ATTR_", _ATTR_DEFAULTS)
            for _, default, _ in [_ATTR_DEFAULTS[attr]] if default
        }
        pool_kwargs["size"] = 0
        pool = sai_thrift_create_buffer_pool(self.client, **pool_kwargs)

        profile = self.create_buffer_profile(pool)
        self.get_buffer_profile_attribute(profile)
        self.remove_buffer_profile(profile)

        sai_thrift_remove_buffer_pool(self.client, pool)

    def create_buffer_profile(self, pool):
        mandatory = get_mandatory_attrs_from_csv("SAI_BUFFER_PROFILE_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_BUFFER_PROFILE_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["pool_id"] = pool
        kwargs["reserved_buffer_size"] = 0
        kwargs["threshold_mode"] = SAI_BUFFER_PROFILE_THRESHOLD_MODE_STATIC
        kwargs["shared_static_th"] = 0
        profile = sai_thrift_create_buffer_profile(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return profile

    def get_buffer_profile_attribute(self, profile):
        verify_object_attributes(self, sai_thrift_get_buffer_profile_attribute, profile, "SAI_BUFFER_PROFILE_ATTR_")

    def remove_buffer_profile(self, profile):
        status = sai_thrift_remove_buffer_profile(self.client, profile)
        self._assert_status_success(status)
