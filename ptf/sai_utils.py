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
Thrift SAI interface basic utils.
"""

import csv
import glob
import inspect
import os
import time
import struct
import socket
import json
import xml.etree.ElementTree as ET

from functools import wraps

from ptf.packet import *
from ptf.testutils import *

from sai_thrift.sai_adapter import *
import sai_thrift.sai_adapter as adapter

from typing import List, Dict
from typing import TYPE_CHECKING


def sai_thrift_query_attribute_enum_values_capability(client,
                                                      obj_type,
                                                      attr_id=None):
    """
    Call the sai_thrift_query_attribute_enum_values_capability() function
    and return the list of supported aattr_is enum capabilities

    Args:
        client (Client): SAI RPC client
        obj_type (enum): SAI object type
        attr_id (attr): SAI attribute name

    Returns:
        list: list of switch object type enum capabilities
    """
    max_cap_no = 20

    enum_cap_list = client.sai_thrift_query_attribute_enum_values_capability(
        obj_type, attr_id, max_cap_no)

    return enum_cap_list


def sai_thrift_object_type_get_availability(client,
                                            obj_type,
                                            attr_id=None,
                                            attr_type=None):
    """
    sai_thrift_object_type_get_availability() RPC client function
    implementation

    Args:
        client (Client): SAI RPC client
        obj_type (enum): SAI object type
        attr_id (attr): SAI attribute name
        attr_type (type): SAI attribute type

    Returns:
        uint: number of available resources with given parameters
    """
    availability_cnt = client.sai_thrift_object_type_get_availability(
        obj_type, attr_id, attr_type)

    return availability_cnt


def sai_thrift_object_type_query(client,
                                 obj_id=None):
    """
    sai_thrift_object_type_query() RPC client function
    implementation

    Args:
        client (Client): SAI RPC client
        obj_id (obj): SAI object id

    Returns:
        uint: object type
    """
    obj_type = client.sai_object_type_query(
        obj_id)

    return obj_type


def sai_thrift_switch_id_query(client,
                               obj_id=None):
    """
    sai_thrift_switch_id_query() RPC client function
    implementation

    Args:
        client (Client): SAI RPC client
        obj_id (obj): SAI object id

    Returns:
        uint: object type
    """
    switch_obj_id = client.sai_switch_id_query(
        obj_id)

    return switch_obj_id


def sai_thrift_api_uninitialize(client):
    """
    sai_thrift_api_uninitialize() RPC client function
    implementation
    Args:
        client (Client): SAI RPC client
    Returns:
        uint: object type
    """
    obj_type = client.sai_thrift_api_uninitialize()

    return obj_type


def sai_thrift_get_debug_counter_port_stats(client, port_oid, counter_ids):
    """
    Get port statistics for given debug counters

    Args:
        client (Client): SAI RPC client
        port_oid (sai_thrift_object_id_t): object_id IN argument
        counter_ids (sai_stat_id_t): list of requested counters

    Returns:
        Dict[str, sai_thrift_uint64_t]: stats
    """

    stats = {}
    counters = client.sai_thrift_get_port_stats(port_oid, counter_ids)

    for i, counter_id in enumerate(counter_ids):
        stats[counter_id] = counters[i]

    return stats


def sai_thrift_get_debug_counter_switch_stats(client, counter_ids):
    """
    Get switch statistics for given debug counters

    Args:
        client (Client): SAI RPC client
        counter_ids (sai_stat_id_t): list of requested counters

    Returns:
        Dict[str, sai_thrift_uint64_t]: stats
    """

    stats = {}
    counters = client.sai_thrift_get_switch_stats(counter_ids)

    for i, counter_id in enumerate(counter_ids):
        stats[counter_id] = counters[i]

    return stats


def sai_ipaddress(addr_str):
    """
    Set SAI IP address, assign appropriate type and return
    sai_thrift_ip_address_t object

    Args:
        addr_str (str): IP address string

    Returns:
        sai_thrift_ip_address_t: object containing IP address family and number
    """

    if '.' in addr_str:
        family = SAI_IP_ADDR_FAMILY_IPV4
        addr = sai_thrift_ip_addr_t(ip4=addr_str)
    if ':' in addr_str:
        family = SAI_IP_ADDR_FAMILY_IPV6
        addr = sai_thrift_ip_addr_t(ip6=addr_str)
    ip_addr = sai_thrift_ip_address_t(addr_family=family, addr=addr)

    return ip_addr


def sai_ipprefix(prefix_str):
    """
    Set IP address prefix and mask and return ip_prefix object

    Args:
        prefix_str (str): IP address and mask string (with slash notation)

    Return:
        sai_thrift_ip_prefix_t: IP prefix object
    """
    addr_mask = prefix_str.split('/')
    if len(addr_mask) != 2:
        print("Invalid IP prefix format")
        return None

    if '.' in prefix_str:
        family = SAI_IP_ADDR_FAMILY_IPV4
        addr = sai_thrift_ip_addr_t(ip4=addr_mask[0])
        mask = num_to_dotted_quad(addr_mask[1])
        mask = sai_thrift_ip_addr_t(ip4=mask)
    if ':' in prefix_str:
        family = SAI_IP_ADDR_FAMILY_IPV6
        addr = sai_thrift_ip_addr_t(ip6=addr_mask[0])
        mask = num_to_dotted_quad(int(addr_mask[1]), ipv4=False)
        mask = sai_thrift_ip_addr_t(ip6=mask)

    ip_prefix = sai_thrift_ip_prefix_t(
        addr_family=family, addr=addr, mask=mask)
    return ip_prefix


def num_to_dotted_quad(address, ipv4=True):
    """
    Helper function to convert the ip address

    Args:
        address (str): IP address
        ipv4 (bool): determines what IP version is handled

    Returns:
        str: formatted IP address
    """
    if ipv4 is True:
        mask = (1 << 32) - (1 << 32 >> int(address))
        return socket.inet_ntop(socket.AF_INET, struct.pack('>L', mask))

    mask = (1 << 128) - (1 << 128 >> int(address))
    i = 0
    result = ''
    for sign in str(hex(mask)[2:]):
        if (i + 1) % 4 == 0:
            result = result + sign + ':'
        else:
            result = result + sign
        i += 1
    return result[:-1]


def open_packet_socket(hostif_name):
    """
    Open a linux socket

    Args:
        hostif_name (str): socket interface name

    Return:
        sock: socket ID
    """
    eth_p_all = 3
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,
                         socket.htons(eth_p_all))
    sock.bind((hostif_name, eth_p_all))
    sock.setblocking(0)

    return sock


def socket_verify_packet(pkt, sock, timeout=2):
    """
    Verify packet was received on a socket

    Args:
        pkt (packet): packet to match with
        sock (int): socket ID
        timeout (int): timeout

    Return:
        bool: True if packet matched
    """
    max_pkt_size = 9100
    timeout = time.time() + timeout
    match = False

    if isinstance(pkt, ptf.mask.Mask):
        if not pkt.is_valid():
            return False

    while time.time() < timeout:
        try:
            packet_from_tap_device = Ether(sock.recv(max_pkt_size))

            if isinstance(pkt, ptf.mask.Mask):
                match = pkt.pkt_match(packet_from_tap_device)
            else:
                match = (str(packet_from_tap_device) == str(pkt))

            if match:
                break

        except BaseException:
            pass

    return match


def delay_wrapper(func, delay=2):
    """
    A wrapper extending given function by a delay

    Args:
        func (function): function to be wrapped
        delay (int): delay period in sec

    Return:
        wrapped_function: wrapped function
    """
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        """
        A wrapper function adding a delay

        Args:
            args (tuple): function arguments
            kwargs (dict): keyword function arguments

        Return:
            status: original function return value
        """
        test_params = test_params_get()
        if 'target' in test_params.keys() and test_params['target'] != "hw":
            time.sleep(delay)

        status = func(*args, **kwargs)
        return status

    return wrapped_function


sai_thrift_flush_fdb_entries = delay_wrapper(sai_thrift_flush_fdb_entries)


def warm_test(is_test_rebooting:bool=False, time_out=60, interval=1):
    """
    Method decorator for the method on warm testing.
    
    Depends on parameters [test_reboot_mode] and [test_reboot_stage].
    Runs different method, test_starting, setUp_post_start and runTest
    
    args:
        is_test_rebooting: whether running the test case when saiserver container shut down
        time_out: check saiserver contianer restart is complete within a 
                  certain time limit.if time limit if exceeded, raise error
        interval: frequency of check
    """
    def _check_run_case(f):
        def test_director(inst, *args):
            if inst.test_reboot_mode == 'warm':
                print("shutdown the swich in warm mode")
                sai_thrift_set_switch_attribute(inst.client, restart_warm=True)
                sai_thrift_set_switch_attribute(inst.client, pre_shutdown=True)
                sai_thrift_remove_switch(inst.client)
                sai_thrift_api_uninitialize(inst.client)
                # write content to reboot-requested
                print("write rebooting to file")
                warm_file = open('/tmp/warm_reboot','w+')
                warm_file.write('rebooting')
                warm_file.close()
                times = 0
                try:
                    while 1:
                        print("reading content in the warm_reboot")
                        warm_file = open('/tmp/warm_reboot','r')
                        txt = warm_file.readline()
                        warm_file.close()                
                        if 'post_reboot_done' in txt:
                            print("warm reboot is done, next, we will run the case")
                            break
                        if is_test_rebooting:
                            print("running in the rebooting stage, text is ", txt)
                            f(inst)
                        times = times + 1
                        time.sleep(interval)
                        print("alreay wait for ",times)
                        if times > time_out:
                            raise Exception("time out")
                except Exception as e:
                    print(e)
                
                inst.createRpcClient()
                inst.warm_start_switch()
            return f(inst)
        return test_director
    return _check_run_case

def query_counter(test, cnt_func, *args, **kwargs):
    """
    Get counter by each counter id for the counter function.
    This method depends on sai_adapater generation pattern.
    The cnt_func name must be with pattern sai_thrift_get_<counter_query_func>
    Then, expect there will be a counter dict with pattern 
        sai_<counter_query_func>_ids_dict
    and a counter list with name pattern
        sai_<counter_query_func>_ids
    Args:
        test: object extends from base test
        cnt_func: counter function
        args: counter function parameters
        kwargs: counter function parameters with name
    return:
        result: dict, counter name and  value
        supported_counters: supported counter name list
        unsupported_counters: unsupported counter name list
    """
    
    fun_name = cnt_func.__name__
    result = {}
    supported_counters = []
    unsupported_counters = []
    if not fun_name.startswith("sai_thrift_get"):
        # cannot get the func name directly
        # it should be a wrapper
        fun_name = inspect.getclosurevars(cnt_func).nonlocals['func'].__name__ 
    if not fun_name.startswith("sai_thrift_get"):
        raise ArgumentError("Cannot get the expected counter query method name")  

    cnt_query_fun_name = fun_name.lstrip("sai_thrift_")
    id_dict_name = "sai_{}_counter_ids_dict".format(cnt_query_fun_name)
    id_list_name = "sai_{}_counter_ids".format(cnt_query_fun_name)
    id_dict = getattr(adapter, id_dict_name)
    id_list = getattr(adapter, id_list_name)

    ignore_api_errors()
    for id in id_list:
        kwargs["counter_ids"] = [id]
        counter = id_dict[id]
        stats = cnt_func(test.client, *args, **kwargs)
        if test.status() == SAI_STATUS_SUCCESS:
            supported_counters.append(counter)
        else:
            unsupported_counters.append(counter)
        result[counter] = stats[counter]
    restore_api_error_code()
    return result


def clear_counter(test, cnt_func, *args, **kwargs):
    """
    Clear counter by each counter id for the counter function.
    This method depends on sai_adapater generation pattern.
    The cnt_func name must be with pattern sai_thrift_clear_<counter_query_func>
    Then, expect there will be a counter dict with pattern 
        sai_<counter_query_func>_ids_dict
    and a counter list with name pattern
        sai_<counter_query_func>_ids
    Args:
        test: object extends from base test
        cnt_func: counter function
        args: counter function parameters
        kwargs: counter function parameters with name
    return:
        supported_counters: supported counter name list
        unsupported_counters: unsupported counter name list
    """
    
    fun_name = cnt_func.__name__
    supported_counters = []
    unsupported_counters = []
    if not fun_name.startswith("sai_thrift_clear"):
        # cannot get the func name directly
        # it should be a wrapper
        fun_name = inspect.getclosurevars(cnt_func).nonlocals['func'].__name__ 
    if not fun_name.startswith("sai_thrift_clear"):
        raise ArgumentError("Cannot get the expected counter clear method name")  

    cnt_clear_fun_name = fun_name.lstrip("sai_thrift_")
    id_dict_name = "sai_{}_counter_ids_dict".format(cnt_clear_fun_name)
    id_list_name = "sai_{}_counter_ids".format(cnt_clear_fun_name)
    id_dict = getattr(adapter, id_dict_name)
    id_list = getattr(adapter, id_list_name)

    ignore_api_errors()
    for id in id_list:
        kwargs["counter_ids"] = [id]
        counter = id_dict[id]
        cnt_func(test.client, *args, **kwargs)
        if test.status() == SAI_STATUS_SUCCESS:
            supported_counters.append(counter)
        else:
            unsupported_counters.append(counter)
    restore_api_error_code()


capture_status = True
expected_code = []
def ignore_api_errors():
    """
    Ignore API errors.
    After run this function, all the API error will be caught
    and will not be raised.

    """
    #print("Ignore all the expect error code and exception captures.")
    global capture_status, expected_code
    capture_status = adapter.CATCH_EXCEPTIONS
    expected_code = adapter.EXPECTED_ERROR_CODE
    adapter.CATCH_EXCEPTIONS = True
    adapter.EXPECTED_ERROR_CODE = []
    return capture_status, expected_code


def restore_api_error_code():
    """
    Restore API error code and catch status.
    """
    #print("Restore all the expect error code and exception captures.")
    global capture_status, expected_code
    adapter.CATCH_EXCEPTIONS = capture_status
    adapter.EXPECTED_ERROR_CODE = expected_code


# ---------------------------------------------------------------------------
# SAI attribute metadata helpers
# ---------------------------------------------------------------------------

# Path to the doxygen XML generated by 'make xml' in meta/.
_SAI_XML_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "meta", "xml",
)

# Path to the SAI attribute defaults CSV at the repo root.
_SAI_ATTR_DEFAULTS_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sai_attr_defaults.csv",
)


def get_mandatory_on_create_attrs(object_type_name, xml_dir=_SAI_XML_DIR):
    """
    Return a sorted list of attribute constant names that are marked
    MANDATORY_ON_CREATE for *object_type_name*.

    The function inspects the doxygen XML files generated from the SAI headers
    (``meta/xml/group__SAI*.xml``).  Each enumvalue element whose
    ``detaileddescription`` contains "MANDATORY_ON_CREATE" corresponds to an
    attribute whose ``sai_thrift_attr_metadata_t.ismandatoryoncreate`` is True.

    Args:
        object_type_name (str): SAI object type without the
            ``SAI_OBJECT_TYPE_`` prefix, e.g. ``"ACL_TABLE_GROUP"``.
        xml_dir (str): Path to the doxygen XML directory.
            Defaults to ``meta/xml/`` relative to the repository root.

    Returns:
        list[str]: Sorted list of mandatory attribute constant names,
        e.g. ``["SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE"]``.

    Example::

        get_mandatory_on_create_attrs("ACL_TABLE_GROUP")
        # -> ["SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE"]

        get_mandatory_on_create_attrs("ACL_TABLE_GROUP_MEMBER")
        # -> ["SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_GROUP_ID",
        #     "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_ACL_TABLE_ID",
        #     "SAI_ACL_TABLE_GROUP_MEMBER_ATTR_PRIORITY"]
    """
    attr_prefix = "SAI_{}_ATTR_".format(object_type_name)
    mandatory = []

    for xml_file in glob.glob(os.path.join(xml_dir, "group__SAI*.xml")):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        xml_text = ET.tostring(root, encoding="unicode")

        if attr_prefix not in xml_text:
            continue

        for enumvalue in root.iter("enumvalue"):
            name_el = enumvalue.find("name")
            if name_el is None or not (name_el.text or "").startswith(attr_prefix):
                continue
            detail_el = enumvalue.find("detaileddescription")
            if detail_el is None:
                continue
            if "MANDATORY_ON_CREATE" in ET.tostring(detail_el, encoding="unicode"):
                mandatory.append(name_el.text)

    return sorted(set(mandatory))


def load_attr_defaults(csv_path=_SAI_ATTR_DEFAULTS_CSV):
    """
    Parse ``sai_attr_defaults.csv`` and return a dict:
        ``{ attribute_name: (type_str, default_str, mandatory) }``

    The ``mandatory`` field is ``True`` when the CSV ``mandatory`` column is
    ``"True"``; ``False`` otherwise.  Rows with an empty ``default_value`` are
    included with ``default_str = ""``.

    Args:
        csv_path (str): Path to the CSV file.
            Defaults to ``sai_attr_defaults.csv`` at the repository root.

    Returns:
        dict: Mapping of attribute name to ``(type_str, default_str, mandatory)``
        tuple.
    """
    defaults = {}
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            mandatory = row.get("mandatory", "False").strip() == "True"
            defaults[row["attribute_name"]] = (
                row["type"],
                row["default_value"],
                mandatory,
            )
    return defaults


def get_mandatory_attrs_from_csv(attr_prefix, attr_defaults=None):
    """
    Return a list of attribute constant names that are marked mandatory
    (``mandatory == True``) in ``sai_attr_defaults.csv`` for the given
    *attr_prefix*.

    This reads the ``mandatory`` column that is populated from the
    ``MANDATORY_ON_CREATE`` flag in the SAI header ``@flags`` annotation by
    ``meta/sai_attr_defaults_csv.py``.

    Args:
        attr_prefix (str): Attribute name prefix, e.g. ``"SAI_ACL_TABLE_ATTR_"``.
        attr_defaults (dict, optional): Pre-loaded defaults from
            :func:`load_attr_defaults`.  Loaded from CSV if ``None``.

    Returns:
        list[str]: Sorted list of mandatory attribute constant names.

    Example::

        get_mandatory_attrs_from_csv("SAI_ACL_TABLE_GROUP_ATTR_")
        # -> ["SAI_ACL_TABLE_GROUP_ATTR_ACL_STAGE"]

        get_mandatory_attrs_from_csv("SAI_ACL_RANGE_ATTR_")
        # -> ["SAI_ACL_RANGE_ATTR_LIMIT", "SAI_ACL_RANGE_ATTR_TYPE"]
    """
    if attr_defaults is None:
        attr_defaults = load_attr_defaults()
    return sorted(
        name
        for name, (_, _, mandatory) in attr_defaults.items()
        if name.startswith(attr_prefix) and mandatory
    )


def get_object_attr_defaults(attr_prefix, attr_defaults=None):
    """
    Return ``{attr_name: (type_str, default_str, mandatory)}`` for all
    attributes whose name starts with *attr_prefix*
    (e.g. ``"SAI_ACL_TABLE_GROUP_ATTR_"``).

    Args:
        attr_prefix (str): Attribute name prefix to filter by.
        attr_defaults (dict, optional): Pre-loaded defaults dict from
            :func:`load_attr_defaults`.  If ``None``, the CSV is loaded
            on every call.

    Returns:
        dict: Filtered attribute defaults for the given prefix.
    """
    if attr_defaults is None:
        attr_defaults = load_attr_defaults()
    return {
        name: val
        for name, val in attr_defaults.items()
        if name.startswith(attr_prefix)
    }


def check_attr_default(test_case, attr_name, type_str, default_str, actual):
    """
    Assert that *actual* (a value returned by a ``sai_thrift_get_*`` call)
    matches the *default_str* from ``sai_attr_defaults.csv``.

    Type dispatch rules:

    ==========================================  ================================
    CSV type                                    Assertion
    ==========================================  ================================
    ``bool``                                    ``== True`` / ``== False``
    ``sai_uint*_t`` / ``sai_int*_t``            ``== int(default_str)``
    ``sai_object_id_t`` + ``SAI_NULL_OBJECT_ID``  ``== SAI_NULL_OBJECT_ID``
    any ``sai_*_t`` + ``SAI_*`` default         ``== getattr(sai_headers, default_str)``
    ``sai_object_list_t`` / ``sai_s32_list_t*`` + ``"empty"``  ``count == 0``
    any type + ``"disabled"``                   ``enable == False``
    ``char``                                    ``== ""``
    empty ``default_str``                       skipped (no default in CSV)
    ==========================================  ================================

    Args:
        test_case: A ``unittest.TestCase`` instance providing assertion methods.
        attr_name (str): Full attribute constant name (used in error messages).
        type_str (str): SAI type string from the CSV ``type`` column.
        default_str (str): Expected default value string from the CSV.
        actual: Value returned by the get adapter function.
    """
    import sai_thrift.sai_headers as _headers

    if default_str == "":
        return

    if type_str == "bool":
        expected = default_str.lower() == "true"
        test_case.assertEqual(
            actual, expected,
            "{}: expected bool {}, got {}".format(attr_name, expected, actual),
        )
        return

    int_types = {
        "sai_uint8_t", "sai_uint16_t", "sai_uint32_t", "sai_uint64_t",
        "sai_int8_t",  "sai_int16_t",  "sai_int32_t",  "sai_int64_t",
    }
    if type_str in int_types:
        expected = int(default_str)
        test_case.assertEqual(
            actual, expected,
            "{}: expected int {}, got {}".format(attr_name, expected, actual),
        )
        return

    if type_str == "sai_object_id_t":
        if default_str == "SAI_NULL_OBJECT_ID":
            test_case.assertEqual(
                actual, SAI_NULL_OBJECT_ID,
                "{}: expected SAI_NULL_OBJECT_ID, got {}".format(attr_name, actual),
            )
        return

    # Any sai_*_t type whose default is a SAI_* constant name is treated as
    # an enum.  This covers all feature-specific enum types generically
    # (ACL, bridge, port, etc.) without maintaining a hard-coded whitelist.
    if type_str.startswith("sai_") and type_str.endswith("_t") \
            and default_str.startswith("SAI_"):
        expected = getattr(_headers, default_str, None)
        if expected is None:
            return
        test_case.assertEqual(
            actual, expected,
            "{}: expected {} ({}), got {}".format(
                attr_name, default_str, repr(expected), repr(actual)
            ),
        )
        return

    if default_str == "empty" and (
        type_str == "sai_object_list_t" or type_str.startswith("sai_s32_list_t")
    ):
        test_case.assertEqual(
            actual.count, 0,
            "{}: expected empty list (count=0), got count={}".format(
                attr_name, actual.count
            ),
        )
        return

    if default_str == "disabled":
        if actual is not None:
            test_case.assertFalse(
                actual.enable,
                "{}: expected disabled (enable=False), got enable={}".format(
                    attr_name, actual.enable
                ),
            )
        return

    if type_str == "char":
        expected = "" if default_str in ('""""""', '""') else default_str.strip('"')
        if actual is not None:
            test_case.assertEqual(
                actual, expected,
                "{}: expected string '{}', got '{}'".format(
                    attr_name, expected, actual
                ),
            )
        return


def verify_object_attributes(test_case, get_fn, oid, attr_prefix,
                              attr_defaults=None, **get_kwargs):
    """
    Call *get_fn* requesting every attribute listed under *attr_prefix* in
    ``sai_attr_defaults.csv``, then assert each returned value matches its
    CSV default via :func:`check_attr_default`.

    Args:
        test_case: A ``unittest.TestCase`` instance.
        get_fn (callable): The ``sai_thrift_get_*_attribute`` adapter function.
        oid (int): The SAI object OID to query.
        attr_prefix (str): Attribute name prefix, e.g. ``"SAI_ACL_TABLE_GROUP_ATTR_"``.
        attr_defaults (dict, optional): Pre-loaded defaults from
            :func:`load_attr_defaults`.  Loaded from CSV if ``None``.
        **get_kwargs: Extra keyword arguments forwarded to *get_fn*
            (e.g. pre-sized list objects).

    Returns:
        dict: The attribute dict returned by *get_fn*, or ``None`` on error.
    """
    object_defaults = get_object_attr_defaults(attr_prefix, attr_defaults)
    sig = inspect.signature(get_fn)

    request_kwargs = {}
    for attr_name, (type_str, _default_str, _mandatory) in object_defaults.items():
        kwarg = attr_name[len(attr_prefix):].lower()
        if kwarg not in sig.parameters:
            continue
        # List-typed attributes require an empty list placeholder so the
        # Thrift serialiser can determine the buffer size.  Passing True
        # causes an AttributeError when the attr_list is written to the wire.
        if type_str == "sai_object_list_t":
            request_kwargs[kwarg] = sai_thrift_object_list_t(count=0, idlist=[])
        elif type_str.startswith("sai_s32_list_t"):
            request_kwargs[kwarg] = sai_thrift_s32_list_t(count=0, int32list=[])
        elif type_str.startswith("sai_u32_list_t"):
            request_kwargs[kwarg] = sai_thrift_u32_list_t(count=0, uint32list=[])
        else:
            request_kwargs[kwarg] = True
    request_kwargs.update(get_kwargs)

    attrs = get_fn(test_case.client, oid, **request_kwargs)
    test_case.assertEqual(
        adapter.status,
        SAI_STATUS_SUCCESS,
        "get {} failed: status {}".format(attr_prefix, adapter.status),
    )

    if attrs is None:
        return attrs

    for attr_name, (type_str, default_str, _mandatory) in object_defaults.items():
        if attr_name in attrs:
            check_attr_default(
                test_case, attr_name, type_str, default_str, attrs[attr_name]
            )

    return attrs


def get_sai_api_functions(feature_keyword):
    """
    Return a sorted list of ``(name, callable)`` tuples for every function in
    ``sai_thrift.sai_adapter`` whose name contains *feature_keyword*.

    Args:
        feature_keyword (str): Substring to match in the function name,
            e.g. ``"_acl_"`` for ACL APIs.

    Returns:
        list[tuple[str, callable]]: Sorted ``(name, fn)`` pairs.

    Example::

        get_sai_api_functions("_acl_")
        # -> [("sai_thrift_create_acl_counter", <function ...>), ...]
    """
    import sai_thrift.sai_adapter as _mod
    return sorted(
        [
            (name, obj)
            for name, obj in inspect.getmembers(_mod, inspect.isfunction)
            if name.startswith("sai_thrift_") and feature_keyword in name
        ]
    )


def get_sai_attribute_constants(module, *prefixes):
    """
    Return ``{name: value}`` for every attribute constant in *module* whose
    name starts with any of *prefixes*.

    Args:
        module: A Python module (e.g. ``sai_thrift.sai_headers``) to inspect.
        *prefixes (str): One or more attribute name prefixes to include,
            e.g. ``"SAI_ACL_TABLE_ATTR_"``, ``"SAI_ACL_ENTRY_ATTR_"``.

    Returns:
        dict: Mapping of constant name to its integer value.

    Example::

        import sai_thrift.sai_headers as h
        get_sai_attribute_constants(h, "SAI_ACL_TABLE_GROUP_ATTR_",
                                       "SAI_ACL_ENTRY_ATTR_")
    """
    return {
        name: getattr(module, name)
        for name in dir(module)
        if any(name.startswith(p) for p in prefixes)
    }
