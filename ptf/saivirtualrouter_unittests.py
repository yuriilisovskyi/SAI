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
SAI PTFv2 Unit Tests for Virtual Router feature (saivirtualrouter.h)
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
class TestVirtualRouterCrud(_AssertMixin, ThriftInterface):
    """
    Virtual Router has no mandatory attributes (all are optional with defaults).
    create/get/set/remove sequence using CSV defaults.
    """

    def runTest(self):
        vr = self.create_virtual_router()
        self.get_virtual_router_attribute(vr)
        self.set_virtual_router_attribute(vr)
        self.remove_virtual_router(vr)

    def create_virtual_router(self):
        # No mandatory attributes from CSV – create with all defaults.
        vr = sai_thrift_create_virtual_router(self.client)
        self._assert_status_success(adapter.status)
        return vr

    def get_virtual_router_attribute(self, vr):
        verify_object_attributes(
            self, sai_thrift_get_virtual_router_attribute,
            vr, "SAI_VIRTUAL_ROUTER_ATTR_",
        )

    def set_virtual_router_attribute(self, vr):
        status = sai_thrift_set_virtual_router_attribute(
            self.client, vr, admin_v4_state=True
        )
        self._assert_status_success(status)

    def remove_virtual_router(self, vr):
        status = sai_thrift_remove_virtual_router(self.client, vr)
        self._assert_status_success(status)
