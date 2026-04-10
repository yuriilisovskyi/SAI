"""
PTF test for inc/saiacl.h — SAI ACL object types.

ACL objects have strict dependency ordering and require Thrift struct arguments
(sai_thrift_acl_field_data_t, sai_thrift_acl_action_data_t, sai_thrift_u32_range_t)
that the generic engine cannot build from plain default strings.  This module
provides a specialized SaiAclTest that follows the same creation pattern used in
the hand-written ptf/saiacl.py tests:

  TABLE_CHAIN_GROUP (standalone)
  TABLE_GROUP       (standalone)
  TABLE             (references stage/bind_points)
  COUNTER           (references table)
  RANGE             (standalone, with proper u32_range_t limit)
  ENTRY             (references table; field_src_ip + action_packet_action)
  TABLE_GROUP_MEMBER (references group + table)

All CRUD functions defined in saiacl_api_attributes.json are exercised.
"""

import os
from sai_api_test import SaiApiTestBase
from sai_thrift.sai_headers import *
from sai_thrift.sai_adapter import *
import sai_thrift.sai_adapter as _adapter
import sai_thrift.ttypes as _ttypes

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiacl_api_attributes.json',
)


class SaiAclTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for ACL object types defined in inc/saiacl.h,
    creating objects in dependency order and using proper Thrift structs where
    required by the SAI API.
    """

    json_path = _JSON

    # Override object_types to control execution order (dependencies first).
    object_types = [
        'SAI_OBJECT_TYPE_ACL_TABLE_CHAIN_GROUP',
        'SAI_OBJECT_TYPE_ACL_TABLE_GROUP',
        'SAI_OBJECT_TYPE_ACL_TABLE',
        'SAI_OBJECT_TYPE_ACL_COUNTER',
        'SAI_OBJECT_TYPE_ACL_RANGE',
        'SAI_OBJECT_TYPE_ACL_ENTRY',
        'SAI_OBJECT_TYPE_ACL_TABLE_GROUP_MEMBER',
    ]

    def runTest(self):
        self._load_json()
        self._results = {}

        # Shared OIDs passed between object types
        self._acl_table_oid = 0
        self._acl_group_oid = 0

        for obj_type in self.object_types:
            if obj_type not in self._data:
                print(f'[WARN] {obj_type} not found in JSON – skipping')
                continue
            self._test_acl_object(obj_type, self._data[obj_type])

        self._report()

    # ------------------------------------------------------------------
    # Per-object-type dispatch
    # ------------------------------------------------------------------

    def _test_acl_object(self, obj_type: str, obj_data: dict):
        """Route each ACL object type to its specialised lifecycle."""
        dispatch = {
            'SAI_OBJECT_TYPE_ACL_TABLE_CHAIN_GROUP': self._test_chain_group,
            'SAI_OBJECT_TYPE_ACL_TABLE_GROUP':       self._test_table_group,
            'SAI_OBJECT_TYPE_ACL_TABLE':             self._test_table,
            'SAI_OBJECT_TYPE_ACL_COUNTER':           self._test_counter,
            'SAI_OBJECT_TYPE_ACL_RANGE':             self._test_range,
            'SAI_OBJECT_TYPE_ACL_ENTRY':             self._test_entry,
            'SAI_OBJECT_TYPE_ACL_TABLE_GROUP_MEMBER': self._test_group_member,
        }
        handler = dispatch.get(obj_type)
        if handler:
            print(f'\n=== {obj_type} ===')
            self._results[obj_type] = {}
            handler(obj_data)
        else:
            self._test_object_type(obj_type, obj_data)

    # ------------------------------------------------------------------
    # ACL_TABLE_CHAIN_GROUP
    # ------------------------------------------------------------------

    def _test_chain_group(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ACL_TABLE_CHAIN_GROUP'
        attrs = obj_data['attributes']

        # create
        self._log_call('sai_thrift_create_acl_table_chain_group', [], {
            'type':  SAI_ACL_TABLE_CHAIN_GROUP_TYPE_SEQUENTIAL,
            'stage': SAI_ACL_TABLE_CHAIN_GROUP_STAGE_0,
        })
        oid, err = self._call(
            sai_thrift_create_acl_table_chain_group,
            type=SAI_ACL_TABLE_CHAIN_GROUP_TYPE_SEQUENTIAL,
            stage=SAI_ACL_TABLE_CHAIN_GROUP_STAGE_0,
        )
        if err:
            self._record(ot, 'sai_thrift_create_acl_table_chain_group', f'FAIL: {err}')
            return
        self._record(ot, 'sai_thrift_create_acl_table_chain_group', 'PASS')
        print(f'  [PASS] sai_thrift_create_acl_table_chain_group → oid={oid}')

        self._run_get_set_remove(
            ot, oid, attrs,
            get_fn=sai_thrift_get_acl_table_chain_group_attribute,
            set_fn=sai_thrift_set_acl_table_chain_group_attribute,
            remove_fn=sai_thrift_remove_acl_table_chain_group,
        )

    # ------------------------------------------------------------------
    # ACL_TABLE_GROUP
    # ------------------------------------------------------------------

    def _test_table_group(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ACL_TABLE_GROUP'
        attrs = obj_data['attributes']

        bind_list = _ttypes.sai_thrift_s32_list_t(
            count=1, int32list=[SAI_ACL_BIND_POINT_TYPE_PORT])
        create_kwargs = {
            'acl_stage':                SAI_ACL_STAGE_INGRESS,
            'acl_bind_point_type_list': bind_list,
            'type':                     SAI_ACL_TABLE_GROUP_TYPE_PARALLEL,
        }
        self._log_call('sai_thrift_create_acl_table_group', [], create_kwargs)
        oid, err = self._call(sai_thrift_create_acl_table_group, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_acl_table_group', f'FAIL: {err}')
            return
        self._acl_group_oid = oid
        self._record(ot, 'sai_thrift_create_acl_table_group', 'PASS')
        print(f'  [PASS] sai_thrift_create_acl_table_group → oid={oid}')

        self._run_get_set_remove(
            ot, oid, attrs,
            get_fn=sai_thrift_get_acl_table_group_attribute,
            set_fn=sai_thrift_set_acl_table_group_attribute,
            remove_fn=sai_thrift_remove_acl_table_group,
            skip_remove=True,   # removed after group_member test
        )

    # ------------------------------------------------------------------
    # ACL_TABLE
    # ------------------------------------------------------------------

    def _test_table(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ACL_TABLE'
        attrs = obj_data['attributes']

        bind_list = _ttypes.sai_thrift_s32_list_t(
            count=1, int32list=[SAI_ACL_BIND_POINT_TYPE_PORT])
        create_kwargs = {
            'acl_stage':                SAI_ACL_STAGE_INGRESS,
            'acl_bind_point_type_list': bind_list,
            'field_src_ip':             True,   # enable at least one match field
        }
        self._log_call('sai_thrift_create_acl_table', [], create_kwargs)
        oid, err = self._call(sai_thrift_create_acl_table, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_acl_table', f'FAIL: {err}')
            return
        self._acl_table_oid = oid
        self._record(ot, 'sai_thrift_create_acl_table', 'PASS')
        print(f'  [PASS] sai_thrift_create_acl_table → oid={oid}')

        self._run_get_set_remove(
            ot, oid, attrs,
            get_fn=sai_thrift_get_acl_table_attribute,
            set_fn=None,   # ACL table has no settable attributes in practice
            remove_fn=sai_thrift_remove_acl_table,
            skip_remove=True,   # removed after entry/counter/member tests
        )

    # ------------------------------------------------------------------
    # ACL_COUNTER
    # ------------------------------------------------------------------

    def _test_counter(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ACL_COUNTER'
        attrs = obj_data['attributes']

        if not self._acl_table_oid:
            self._record(ot, 'sai_thrift_create_acl_counter',
                         'SKIP: no ACL table OID available')
            return

        create_kwargs = {
            'table_id':             self._acl_table_oid,
            'enable_packet_count':  True,
            'enable_byte_count':    True,
        }
        self._log_call('sai_thrift_create_acl_counter', [], create_kwargs)
        oid, err = self._call(sai_thrift_create_acl_counter, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_acl_counter', f'FAIL: {err}')
            return
        self._record(ot, 'sai_thrift_create_acl_counter', 'PASS')
        print(f'  [PASS] sai_thrift_create_acl_counter → oid={oid}')

        self._run_get_set_remove(
            ot, oid, attrs,
            get_fn=sai_thrift_get_acl_counter_attribute,
            set_fn=sai_thrift_set_acl_counter_attribute,
            remove_fn=sai_thrift_remove_acl_counter,
        )

    # ------------------------------------------------------------------
    # ACL_RANGE
    # ------------------------------------------------------------------

    def _test_range(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ACL_RANGE'
        attrs = obj_data['attributes']

        u32range = _ttypes.sai_thrift_u32_range_t(min=0, max=65535)
        create_kwargs = {
            'type':  SAI_ACL_RANGE_TYPE_L4_DST_PORT_RANGE,
            'limit': u32range,
        }
        self._log_call('sai_thrift_create_acl_range', [], create_kwargs)
        oid, err = self._call(sai_thrift_create_acl_range, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_acl_range', f'FAIL: {err}')
            return
        self._record(ot, 'sai_thrift_create_acl_range', 'PASS')
        print(f'  [PASS] sai_thrift_create_acl_range → oid={oid}')

        self._run_get_set_remove(
            ot, oid, attrs,
            get_fn=sai_thrift_get_acl_range_attribute,
            set_fn=None,
            remove_fn=sai_thrift_remove_acl_range,
        )

    # ------------------------------------------------------------------
    # ACL_ENTRY
    # ------------------------------------------------------------------

    def _test_entry(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ACL_ENTRY'
        attrs = obj_data['attributes']

        if not self._acl_table_oid:
            self._record(ot, 'sai_thrift_create_acl_entry',
                         'SKIP: no ACL table OID available')
            return

        # Match field: src_ip with an IP/mask
        src_ip_field = _ttypes.sai_thrift_acl_field_data_t(
            enable=True,
            data=_ttypes.sai_thrift_acl_field_data_data_t(ip4='10.0.0.1'),
            mask=_ttypes.sai_thrift_acl_field_data_mask_t(ip4='255.255.255.255'),
        )
        # Action: drop
        pkt_action = _ttypes.sai_thrift_acl_action_data_t(
            enable=True,
            parameter=_ttypes.sai_thrift_acl_action_parameter_t(
                s32=SAI_PACKET_ACTION_DROP),
        )
        create_kwargs = {
            'table_id':            self._acl_table_oid,
            'priority':            10,
            'admin_state':         True,
            'field_src_ip':        src_ip_field,
            'action_packet_action': pkt_action,
        }
        self._log_call('sai_thrift_create_acl_entry', [], create_kwargs)
        oid, err = self._call(sai_thrift_create_acl_entry, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_acl_entry', f'FAIL: {err}')
            return
        self._record(ot, 'sai_thrift_create_acl_entry', 'PASS')
        print(f'  [PASS] sai_thrift_create_acl_entry → oid={oid}')

        self._run_get_set_remove(
            ot, oid, attrs,
            get_fn=sai_thrift_get_acl_entry_attribute,
            set_fn=sai_thrift_set_acl_entry_attribute,
            remove_fn=sai_thrift_remove_acl_entry,
        )

    # ------------------------------------------------------------------
    # ACL_TABLE_GROUP_MEMBER
    # ------------------------------------------------------------------

    def _test_group_member(self, obj_data: dict):
        ot = 'SAI_OBJECT_TYPE_ACL_TABLE_GROUP_MEMBER'
        attrs = obj_data['attributes']

        if not self._acl_group_oid or not self._acl_table_oid:
            self._record(ot, 'sai_thrift_create_acl_table_group_member',
                         'SKIP: no ACL group or table OID available')
            return

        create_kwargs = {
            'acl_table_group_id': self._acl_group_oid,
            'acl_table_id':       self._acl_table_oid,
            'priority':           1,
        }
        self._log_call('sai_thrift_create_acl_table_group_member', [], create_kwargs)
        oid, err = self._call(sai_thrift_create_acl_table_group_member, **create_kwargs)
        if err:
            self._record(ot, 'sai_thrift_create_acl_table_group_member', f'FAIL: {err}')
        else:
            self._record(ot, 'sai_thrift_create_acl_table_group_member', 'PASS')
            print(f'  [PASS] sai_thrift_create_acl_table_group_member → oid={oid}')

            self._run_get_set_remove(
                ot, oid, attrs,
                get_fn=sai_thrift_get_acl_table_group_member_attribute,
                set_fn=sai_thrift_set_acl_table_group_member_attribute,
                remove_fn=sai_thrift_remove_acl_table_group_member,
            )

        # Clean up table and group (deferred from earlier)
        if self._acl_table_oid:
            self._log_call('sai_thrift_remove_acl_table',
                           [self._acl_table_oid], {})
            _, err = self._call(sai_thrift_remove_acl_table, self._acl_table_oid)
            if err:
                print(f'  [WARN] remove_acl_table: {err}')
            self._acl_table_oid = 0

        if self._acl_group_oid:
            self._log_call('sai_thrift_remove_acl_table_group',
                           [self._acl_group_oid], {})
            _, err = self._call(sai_thrift_remove_acl_table_group, self._acl_group_oid)
            if err:
                print(f'  [WARN] remove_acl_table_group: {err}')
            self._acl_group_oid = 0

    # ------------------------------------------------------------------
    # Shared get / set / remove helper
    # ------------------------------------------------------------------

    def _run_get_set_remove(self, obj_type, oid, attrs,
                            get_fn, set_fn, remove_fn,
                            skip_remove=False):
        """
        Run get, set, and remove using the base engine helpers,
        passing the known OID directly rather than relying on ctx.
        """
        ctx = {'oid': oid}

        # get
        fn_get_name = get_fn.__name__
        fn_get = self._resolve(fn_get_name)
        if fn_get:
            self._exec_get(fn_get_name, attrs, ctx, obj_type)

        # set
        if set_fn:
            fn_set_name = set_fn.__name__
            fn_set = self._resolve(fn_set_name)
            if fn_set:
                self._exec_set(fn_set_name, attrs, ctx, obj_type)

        # remove
        if not skip_remove and remove_fn:
            fn_rm_name = remove_fn.__name__
            self._exec_remove(fn_rm_name, ctx, obj_type)
