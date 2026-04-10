"""
PTF test for inc/saineighbor.h — SAI neighbor entry.

Neighbor entries require a pre-built sai_thrift_neighbor_entry_t key struct:
    neighbor_entry = sai_thrift_neighbor_entry_t(
        rif_id=rif_oid, ip_address=sai_ipaddress('192.168.1.1'))
    sai_thrift_create_neighbor_entry(client, neighbor_entry, dst_mac_address='00:...')

A VLAN router interface is created on the default VLAN to provide rif_id.
Pattern from ptf/saineighbor.py and ptf/sairoute.py.
"""

import os
import sys

_PTF_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PTF_DIR not in sys.path:
    sys.path.insert(0, _PTF_DIR)

from sai_api_test import SaiApiTestBase
from sai_thrift.sai_headers import *
from sai_thrift.sai_adapter import *
from sai_utils import sai_ipaddress
import sai_thrift.ttypes as _ttypes

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saineighbor_api_attributes.json',
)

_NEIGHBOR_IP  = '192.168.100.1'
_NEIGHBOR_MAC = '00:11:22:33:44:55'


class SaiNeighborTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for SAI_OBJECT_TYPE_NEIGHBOR_ENTRY.
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_NEIGHBOR_ENTRY']

    def runTest(self):
        self._load_json()
        self._results = {}
        self._test_neighbor_entry(self._data['SAI_OBJECT_TYPE_NEIGHBOR_ENTRY'])
        self._report()

    def _test_neighbor_entry(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_NEIGHBOR_ENTRY'
        attrs = obj_data['attributes']
        self._results[ot] = {}
        print(f'\n=== {ot} ===')

        sw_ctx = self._discover_switch_context()
        if not sw_ctx['default_vrf'] or not sw_ctx['default_vlan_id']:
            self._record(ot, 'sai_thrift_create_neighbor_entry',
                         'SKIP: cannot discover default_vrf or default_vlan_id')
            return

        # Create a VLAN router interface on the default VLAN to provide rif_id
        rif_kwargs = {
            'type':              SAI_ROUTER_INTERFACE_TYPE_VLAN,
            'virtual_router_id': sw_ctx['default_vrf'],
            'vlan_id':           sw_ctx['default_vlan_id'],
        }
        self._log_call('sai_thrift_create_router_interface', [], rif_kwargs)
        rif_oid, err = self._call(sai_thrift_create_router_interface, **rif_kwargs)
        if err or not rif_oid:
            self._record(ot, 'sai_thrift_create_neighbor_entry',
                         f'SKIP: cannot create router interface: {err}')
            return

        try:
            neighbor_entry = _ttypes.sai_thrift_neighbor_entry_t(
                switch_id=sw_ctx['switch_id'],
                rif_id=rif_oid,
                ip_address=sai_ipaddress(_NEIGHBOR_IP),
            )

            # create
            create_kwargs = {'dst_mac_address': _NEIGHBOR_MAC}
            self._log_call('sai_thrift_create_neighbor_entry',
                           [neighbor_entry], create_kwargs)
            _, err = self._call(
                sai_thrift_create_neighbor_entry, neighbor_entry, **create_kwargs)
            if err:
                self._record(ot, 'sai_thrift_create_neighbor_entry', f'FAIL: {err}')
                return
            self._record(ot, 'sai_thrift_create_neighbor_entry', 'PASS')
            print(f'  [PASS] sai_thrift_create_neighbor_entry')

            # get
            self._exec_entry_get('sai_thrift_get_neighbor_entry_attribute',
                                 attrs, neighbor_entry, ot)

            # set
            self._exec_entry_set('sai_thrift_set_neighbor_entry_attribute',
                                 attrs, neighbor_entry, ot)

            # remove
            self._log_call('sai_thrift_remove_neighbor_entry', [neighbor_entry], {})
            _, err = self._call(sai_thrift_remove_neighbor_entry, neighbor_entry)
            if err:
                self._record(ot, 'sai_thrift_remove_neighbor_entry', f'FAIL: {err}')
            else:
                self._record(ot, 'sai_thrift_remove_neighbor_entry', 'PASS')
                print(f'  [PASS] sai_thrift_remove_neighbor_entry')

        finally:
            # Remove the temporary RIF
            self._log_call('sai_thrift_remove_router_interface', [rif_oid], {})
            sai_thrift_remove_router_interface(self.client, rif_oid)
