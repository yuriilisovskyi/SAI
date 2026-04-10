"""
PTF test for inc/saifdb.h — SAI FDB entry.

FDB entries require a pre-built sai_thrift_fdb_entry_t key struct:
    fdb_entry = sai_thrift_fdb_entry_t(
        switch_id=..., mac_address="00:11:22:33:44:55", bv_id=default_vlan_id)
    sai_thrift_create_fdb_entry(client, fdb_entry, type=SAI_FDB_ENTRY_TYPE_STATIC, ...)

Pattern from ptf/saifdb.py.
"""

import os
from sai_api_test import SaiApiTestBase
from sai_thrift.sai_headers import *
from sai_thrift.sai_adapter import *
import sai_thrift.ttypes as _ttypes

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saifdb_api_attributes.json',
)

_TEST_MAC = '00:11:22:33:44:55'


class SaiFdbTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for SAI_OBJECT_TYPE_FDB_ENTRY.
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_FDB_ENTRY']

    def runTest(self):
        self._load_json()
        self._results = {}
        self._test_fdb_entry(self._data['SAI_OBJECT_TYPE_FDB_ENTRY'])
        self._report()

    def _test_fdb_entry(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_FDB_ENTRY'
        attrs = obj_data['attributes']
        self._results[ot] = {}
        print(f'\n=== {ot} ===')

        sw_ctx = self._discover_switch_context()

        fdb_entry = _ttypes.sai_thrift_fdb_entry_t(
            switch_id=sw_ctx['switch_id'],
            mac_address=_TEST_MAC,
            bv_id=sw_ctx['default_vlan_id'],   # SAI_NULL_OBJECT_ID (0) if not found
        )

        # create
        create_kwargs = {
            'type':          SAI_FDB_ENTRY_TYPE_STATIC,
            'packet_action': SAI_PACKET_ACTION_FORWARD,
        }
        self._log_call('sai_thrift_create_fdb_entry', [fdb_entry], create_kwargs)
        _, err = self._call(sai_thrift_create_fdb_entry, fdb_entry, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_fdb_entry', f'FAIL: {err}')
            return
        self._record(ot, 'sai_thrift_create_fdb_entry', 'PASS')
        print(f'  [PASS] sai_thrift_create_fdb_entry')

        # get
        self._exec_entry_get('sai_thrift_get_fdb_entry_attribute', attrs, fdb_entry, ot)

        # set
        self._exec_entry_set('sai_thrift_set_fdb_entry_attribute', attrs, fdb_entry, ot)

        # remove
        self._log_call('sai_thrift_remove_fdb_entry', [fdb_entry], {})
        _, err = self._call(sai_thrift_remove_fdb_entry, fdb_entry)
        if err:
            self._record(ot, 'sai_thrift_remove_fdb_entry', f'FAIL: {err}')
        else:
            self._record(ot, 'sai_thrift_remove_fdb_entry', 'PASS')
            print(f'  [PASS] sai_thrift_remove_fdb_entry')
