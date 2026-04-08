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

"""SAI PTFv2 Unit Tests for Mirror Session feature (saimirror.h)"""

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


class TestMirrorSessionCrud(_AssertMixin, ThriftInterface):
    """
import os as _os
import sys as _sys
# Add ptf/ to sys.path so sai_base_test and sai_utils can be found when
# this file is run from ptf/unittests/.
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))


    Mirror Session mandatory attrs from CSV (TYPE=LOCAL, the CSV default):
      SAI_MIRROR_SESSION_ATTR_TYPE         (default: SAI_MIRROR_SESSION_TYPE_LOCAL)
      SAI_MIRROR_SESSION_ATTR_MONITOR_PORT (OID, no default – use first active port)

    Other mandatory attrs (SRC/DST IP, MAC, GRE etc.) apply only to
    SAI_MIRROR_SESSION_TYPE_REMOTE and SAI_MIRROR_SESSION_TYPE_ENHANCED_REMOTE;
    they are not required for LOCAL mirroring.
    """

    def runTest(self):
        attr = sai_thrift_get_switch_attribute(self.client, number_of_active_ports=True)
        num_ports = attr["number_of_active_ports"]
        attr = sai_thrift_get_switch_attribute(
            self.client, port_list=sai_thrift_object_list_t(idlist=[], count=num_ports))
        monitor_port = attr["port_list"].idlist[0]

        session = self.create_mirror_session(monitor_port)
        self.get_mirror_session_attribute(session)
        self.set_mirror_session_attribute(session, monitor_port)
        self.remove_mirror_session(session)

    def create_mirror_session(self, monitor_port):
        mandatory = get_mandatory_attrs_from_csv("SAI_MIRROR_SESSION_ATTR_", _ATTR_DEFAULTS)
        kwargs = {}
        for attr in mandatory:
            _t, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_MIRROR_SESSION_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # Only TYPE and MONITOR_PORT are required for LOCAL sessions.
        kwargs["type"] = SAI_MIRROR_SESSION_TYPE_LOCAL
        kwargs["monitor_port"] = monitor_port
        session = sai_thrift_create_mirror_session(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return session

    def get_mirror_session_attribute(self, session):
        verify_object_attributes(self, sai_thrift_get_mirror_session_attribute, session, "SAI_MIRROR_SESSION_ATTR_")

    def set_mirror_session_attribute(self, session, monitor_port):
        status = sai_thrift_set_mirror_session_attribute(
            self.client, session, monitor_port=monitor_port
        )
        self._assert_status_success(status)

    def remove_mirror_session(self, session):
        status = sai_thrift_remove_mirror_session(self.client, session)
        self._assert_status_success(status)
