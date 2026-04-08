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
SAI PTFv2 Unit Tests for LAG feature (sailag.h)
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
class TestLagCrud(_AssertMixin, ThriftInterface):
    """LAG has no mandatory attributes; all defaults from CSV."""

    def runTest(self):
        lag = self.create_lag()
        self.get_lag_attribute(lag)
        self.set_lag_attribute(lag)
        self.remove_lag(lag)

    def create_lag(self):
        lag = sai_thrift_create_lag(self.client)
        self._assert_status_success(adapter.status)
        return lag

    def get_lag_attribute(self, lag):
        verify_object_attributes(
            self, sai_thrift_get_lag_attribute, lag, "SAI_LAG_ATTR_",
        )

    def set_lag_attribute(self, lag):
        status = sai_thrift_set_lag_attribute(self.client, lag, port_vlan_id=1)
        self._assert_status_success(status)

    def remove_lag(self, lag):
        status = sai_thrift_remove_lag(self.client, lag)
        self._assert_status_success(status)


class TestLagMemberCrud(_AssertMixin, ThriftInterface):
    """
    LAG Member mandatory attrs from CSV:
      SAI_LAG_MEMBER_ATTR_LAG_ID   (OID, no default)
      SAI_LAG_MEMBER_ATTR_PORT_ID  (OID, no default)
    """

    def runTest(self):
        lag = sai_thrift_create_lag(self.client)

        attr = sai_thrift_get_switch_attribute(
            self.client, number_of_active_ports=True
        )
        num_ports = attr["number_of_active_ports"]
        attr = sai_thrift_get_switch_attribute(
            self.client,
            port_list=sai_thrift_object_list_t(idlist=[], count=num_ports),
        )
        port_id = attr["port_list"].idlist[0]

        member = self.create_lag_member(lag, port_id)
        self.get_lag_member_attribute(member)
        self.set_lag_member_attribute(member)
        self.remove_lag_member(member)

        sai_thrift_remove_lag(self.client, lag)

    def create_lag_member(self, lag, port_id):
        mandatory = get_mandatory_attrs_from_csv("SAI_LAG_MEMBER_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_LAG_MEMBER_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        kwargs["lag_id"] = lag
        kwargs["port_id"] = port_id
        member = sai_thrift_create_lag_member(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return member

    def get_lag_member_attribute(self, member):
        verify_object_attributes(
            self, sai_thrift_get_lag_member_attribute, member, "SAI_LAG_MEMBER_ATTR_",
        )

    def set_lag_member_attribute(self, member):
        status = sai_thrift_set_lag_member_attribute(
            self.client, member, egress_disable=False
        )
        self._assert_status_success(status)

    def remove_lag_member(self, member):
        status = sai_thrift_remove_lag_member(self.client, member)
        self._assert_status_success(status)
