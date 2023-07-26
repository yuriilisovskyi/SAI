#include <stdio.h>
#include "sai.h"

const char* test_profile_get_value(
    _In_ sai_switch_profile_id_t profile_id,
    _In_ const char* variable)
{
    return 0;
}

int test_profile_get_next_value(
    _In_ sai_switch_profile_id_t profile_id,
    _Out_ const char** variable,
    _Out_ const char** value)
{
    return -1;
}

const service_method_table_t test_services = {
    test_profile_get_value,
    test_profile_get_next_value
};

int main()
{
    sai_status_t              status;
    sai_lag_api_t            *lag_api;
    sai_object_id_t           lag1_oid;
    sai_object_id_t           lag2_oid;
    sai_switch_api_t         *switch_api;
    sai_object_id_t           vr_oid;
    sai_attribute_t           attrs[2];
    sai_switch_notification_t notifications;
    sai_object_id_t           port_list[64];
    sai_object_id_t           lag_member1_oid;
    sai_object_id_t           lag_member2_oid;
    sai_object_id_t           lag_member3_oid;
    sai_object_id_t           lag_member4_oid;

    status = sai_api_initialize(0, &test_services);
    status = sai_api_query(SAI_API_SWITCH, (void**)&switch_api);
    status = switch_api->initialize_switch(0, "HW_ID", 0, &notifications);
    attrs[0].id = SAI_SWITCH_ATTR_PORT_LIST;
    attrs[0].value.objlist.list = port_list;
    attrs[0].value.objlist.count = 64;
    status = switch_api->get_switch_attribute(1, attrs);
    for (int32_t ii = 0; ii < attrs[0].value.objlist.count; ii++) {
        printf("Port #%d OID: 0x%lX\n", ii, attrs[0].value.objlist.list[ii]);
    }
    status = sai_api_query(SAI_API_LAG, (void**)&lag_api);
    if (status != SAI_STATUS_SUCCESS) {
	printf("Failed to query LAG API: %d\n", status);
	return 1;
    }
    status = lag_api->create_lag(&lag1_oid, 0, NULL);
    status = lag_api->create_lag(&lag2_oid, 0, NULL);

    sai_attribute_t lag_member_attrs[2];
    lag_member_attrs[0].id = SAI_LAG_MEMBER_ATTR_LAG_ID;
    lag_member_attrs[1].id = SAI_LAG_MEMBER_ATTR_PORT;
    lag_member_attrs[0].value.objid = lag1_oid;
    lag_member_attrs[1].value.objid = port_list[0];
    lag_api->create_lag_member(&lag_member1_oid, 2, *lab_member_attrs);
    lag_member_attrs[1].value.objid = port_list[1];
    lag_api->create_lag_member(&lag_member2_oid, 2, *lab_member_attrs);

    lag_member_attrs[0].value.objid = lag2_oid;
    lag_member_attrs[1].value.objid = port_list[2];
    lag_api->create_lag_member(&lag_member1_oid, 2, *lab_member_attrs);
    lag_member_attrs[1].value.objid = port_list[3];
    lag_api->create_lag_member(&lag_member2_oid, 0, *lab_member_attrs);

    lag_api->get_lag_attribute(lag1_oid, SAI_LAG_ATTR_PORT_LIST);
    lag_api->get_lag_attribute(lag2_oid, SAI_LAG_ATTR_PORT_LIST);

    lag_api->get_lag_member_attribute(lag_member1_oid, SAI_LAG_MEMBER_ATTR_LAG_ID);
    lag_api->get_lag_member_attribute(lag_member3_oid, SAI_LAG_MEMBER_ATTR_PORT);

    lag_api->remove_lag_member(lag_member2_oid);
    lag_api->get_lag_attribute(lag1_oid, SAI_LAG_ATTR_PORT_LIST);

    lag_api->remove_lag_member(lag_member3_oid);
    lag_api->get_lag_attribute(lag2_oid, SAI_LAG_ATTR_PORT_LIST);

    lag_api->remove_lag_member(lag_member1_oid);
    lag_api->remove_lag_member(lag_member4_oid);

    lag_api->remove_lag(lag2_oid);
    lag_api->remove_lag(lag1_oid);

    switch_api->shutdown_switch(0);
    status = sai_api_uninitialize();
    return 0;
}
