"""
PTF test for inc/sairoute.h — SAI route entry.

Route entries require a pre-built sai_thrift_route_entry_t key struct:
    route_entry = sai_thrift_route_entry_t(
        vr_id=default_vrf, destination=sai_ipprefix('10.0.0.0/24'))
    sai_thrift_create_route_entry(client, route_entry, packet_action=SAI_PACKET_ACTION_DROP)

Pattern from ptf/sairoute.py.
"""

import os
import sys

_PTF_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PTF_DIR not in sys.path:
    sys.path.insert(0, _PTF_DIR)

from sai_api_test import SaiApiTestBase
from sai_thrift.sai_headers import *
from sai_thrift.sai_adapter import *
from sai_utils import sai_ipprefix
import sai_thrift.ttypes as _ttypes

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'sairoute_api_attributes.json',
)

_ROUTE_PREFIX = '192.168.200.0/24'


class SaiRouteTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for SAI_OBJECT_TYPE_ROUTE_ENTRY.
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_ROUTE_ENTRY']

    def runTest(self):
        self._load_json()
        self._results = {}
        self._test_route_entry(self._data['SAI_OBJECT_TYPE_ROUTE_ENTRY'])
        self._report()

    def _test_route_entry(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ROUTE_ENTRY'
        attrs = obj_data['attributes']
        self._results[ot] = {}
        print(f'\n=== {ot} ===')

        sw_ctx = self._discover_switch_context()

        route_entry = _ttypes.sai_thrift_route_entry_t(
            switch_id=sw_ctx['switch_id'],
            vr_id=sw_ctx['default_vrf'],
            destination=sai_ipprefix(_ROUTE_PREFIX),
        )

        # create — use DROP action so no next-hop OID is required
        create_kwargs = {'packet_action': SAI_PACKET_ACTION_DROP}
        self._log_call('sai_thrift_create_route_entry', [route_entry], create_kwargs)
        _, err = self._call(sai_thrift_create_route_entry, route_entry, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_route_entry', f'FAIL: {err}')
            return
        self._record(ot, 'sai_thrift_create_route_entry', 'PASS')
        print(f'  [PASS] sai_thrift_create_route_entry')

        # get
        self._exec_entry_get('sai_thrift_get_route_entry_attribute',
                             attrs, route_entry, ot)

        # set
        self._exec_entry_set('sai_thrift_set_route_entry_attribute',
                             attrs, route_entry, ot)

        # remove
        self._log_call('sai_thrift_remove_route_entry', [route_entry], {})
        _, err = self._call(sai_thrift_remove_route_entry, route_entry)
        if err:
            self._record(ot, 'sai_thrift_remove_route_entry', f'FAIL: {err}')
        else:
            self._record(ot, 'sai_thrift_remove_route_entry', 'PASS')
            print(f'  [PASS] sai_thrift_remove_route_entry')

        # bulk operations require custom entry lists
        for bulk_fn in ['sai_thrift_bulk_create_route_entry',
                        'sai_thrift_bulk_get_route_entry_attribute',
                        'sai_thrift_bulk_set_route_entry_attribute',
                        'sai_thrift_bulk_remove_route_entry']:
            self._record(ot, bulk_fn, 'SKIP: bulk operations require custom entry lists')
