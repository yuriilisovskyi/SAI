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
SAI PTFv2 Unit Tests for Bridge Feature

Validates the SAI Bridge implementation by:
  1. Discovering all SAI Bridge APIs and attribute constants from
     test/saithriftv2/build/lib/sai_thrift (sai_adapter + sai_headers).
  2. Verifying that each CRUD API call with mandatory attributes returns
     SAI_STATUS_SUCCESS against a running SAI implementation.
  3. For get calls: iterating over ALL attributes defined in
     sai_attr_defaults.csv for the object type and comparing each
     returned value against the default specified in that CSV.

SAI objects covered (from inc/saibridge.h):
  - Bridge      (create / get / set / remove)
  - Bridge Port (create / get / set / remove)

Each test class inherits from ThriftInterface (sai_base_test.py) which
sets up the Thrift RPC connection via setUp/tearDown.  Each class defines a
runTest method that calls create, get, set, and remove helper methods in
sequence using a single SAI object.

Mandatory-on-create attributes (per @flags in saibridge.h):
  Bridge:
    SAI_BRIDGE_ATTR_TYPE

  Bridge Port (TYPE == SAI_BRIDGE_PORT_TYPE_PORT):
    SAI_BRIDGE_PORT_ATTR_TYPE
    SAI_BRIDGE_PORT_ATTR_PORT_ID   (conditional: TYPE == PORT or SUB_PORT)

Prerequisites:
  1. Build the sai_thrift package:
       export SAITHRIFTV2=y
       make saithrift-build
       cd test/saithriftv2 && python3 setup.py install

  2. Start the SAI RPC server (saiserver) with a SAI library loaded.
     The test uses the first active port available on the switch.

Run with:
    ptf --test-dir ptf saibridge_unittests
or:
    python3 -m pytest ptf/saibridge_unittests.py -v
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

# Pre-load attribute defaults once at import time.
_ATTR_DEFAULTS = load_attr_defaults()


# ---------------------------------------------------------------------------
# Shared status assertion mixin
# ---------------------------------------------------------------------------

class _SaiBridgeAssertMixin:
    def _assert_status_success(self, status, msg=""):
        self.assertEqual(
            status,
            SAI_STATUS_SUCCESS,
            msg or "Expected SAI_STATUS_SUCCESS (0), got {}".format(status),
        )


# ===========================================================================
# Test Class 1: Discover Bridge APIs and attributes from sai_thrift
class TestBridgeCrud(_SaiBridgeAssertMixin, ThriftInterface):
    """
    Validates create / get / set / remove for Bridge.
    Mandatory attributes are created with their CSV default values so that
    get can verify the returned values match those same defaults.
    get iterates all SAI_BRIDGE_ATTR_* attributes from sai_attr_defaults.csv
    and validates each returned value against its defined default.

    Mandatory-on-create: SAI_BRIDGE_ATTR_TYPE (default: SAI_BRIDGE_TYPE_1Q)
    """

    def runTest(self):
        bridge = self.create_bridge()
        self.get_bridge_attribute(bridge)
        self.set_bridge_attribute(bridge)
        self.remove_bridge(bridge)

    def create_bridge(self):
        # Build kwargs from CSV mandatory attributes using their default values.
        # SAI_BRIDGE_ATTR_TYPE default is SAI_BRIDGE_TYPE_1Q.
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_BRIDGE_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_BRIDGE_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        bridge = sai_thrift_create_bridge(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return bridge

    def get_bridge_attribute(self, bridge):
        verify_object_attributes(
            self,
            sai_thrift_get_bridge_attribute,
            bridge,
            "SAI_BRIDGE_ATTR_",
        )

    def set_bridge_attribute(self, bridge):
        status = sai_thrift_set_bridge_attribute(
            self.client, bridge, learn_disable=True
        )
        self._assert_status_success(status)

    def remove_bridge(self, bridge):
        status = sai_thrift_remove_bridge(self.client, bridge)
        self._assert_status_success(status)


# ===========================================================================
# Test Class 3: Bridge Port CRUD
# ===========================================================================

class TestBridgePortCrud(_SaiBridgeAssertMixin, ThriftInterface):
    """
    Validates create / get / set / remove for Bridge Port.
    Mandatory attributes are created with their CSV default values.
    get iterates all SAI_BRIDGE_PORT_ATTR_* attributes from
    sai_attr_defaults.csv and validates each returned value against its
    defined default.

    Mandatory-on-create (TYPE == SAI_BRIDGE_PORT_TYPE_PORT, the CSV default):
      SAI_BRIDGE_PORT_ATTR_TYPE     (default: SAI_BRIDGE_PORT_TYPE_PORT)
      SAI_BRIDGE_PORT_ATTR_PORT_ID  (OID, no default – supplied at runtime)

    Prerequisite: first active switch port retrieved via SAI_SWITCH_ATTR_PORT_LIST.
    """

    def runTest(self):
        # Retrieve first active port to use as PORT_ID.
        attr = sai_thrift_get_switch_attribute(
            self.client, number_of_active_ports=True
        )
        num_ports = attr["number_of_active_ports"]

        attr = sai_thrift_get_switch_attribute(
            self.client,
            port_list=sai_thrift_object_list_t(idlist=[], count=num_ports),
        )
        port_id = attr["port_list"].idlist[0]

        bridge_port = self.create_bridge_port(port_id)
        self.get_bridge_port_attribute(bridge_port)
        self.set_bridge_port_attribute(bridge_port)
        self.remove_bridge_port(bridge_port)

    def create_bridge_port(self, port_id):
        # Build kwargs from CSV mandatory attributes using their default values.
        # Attributes with no CSV default (OID types) are supplied at runtime.
        # For TYPE=SAI_BRIDGE_PORT_TYPE_PORT (the default), only TYPE and
        # PORT_ID are required; other conditionally-mandatory attrs
        # (BRIDGE_ID, VLAN_ID, RIF_ID, TUNNEL_ID, NEXT_HOP_GROUP_ID)
        # apply to other TYPE values and are omitted.
        mandatory = get_mandatory_attrs_from_csv(
            "SAI_BRIDGE_PORT_ATTR_", _ATTR_DEFAULTS
        )
        kwargs = {}
        for attr in mandatory:
            _type, default, _m = _ATTR_DEFAULTS[attr]
            kwarg = attr[len("SAI_BRIDGE_PORT_ATTR_"):].lower()
            if default:
                kwargs[kwarg] = getattr(sai_headers, default, default)
        # Supply port_id (mandatory OID with no CSV default).
        kwargs["port_id"] = port_id
        bridge_port = sai_thrift_create_bridge_port(self.client, **kwargs)
        self._assert_status_success(adapter.status)
        return bridge_port

    def get_bridge_port_attribute(self, bridge_port):
        verify_object_attributes(
            self,
            sai_thrift_get_bridge_port_attribute,
            bridge_port,
            "SAI_BRIDGE_PORT_ATTR_",
        )

    def set_bridge_port_attribute(self, bridge_port):
        status = sai_thrift_set_bridge_port_attribute(
            self.client, bridge_port, admin_state=True
        )
        self._assert_status_success(status)

    def remove_bridge_port(self, bridge_port):
        status = sai_thrift_remove_bridge_port(self.client, bridge_port)
        self._assert_status_success(status)
