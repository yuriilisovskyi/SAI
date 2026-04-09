"""
Auto-generated PTF test for inc/saiacl.h.

Validates all SAI object types defined in inc/saiacl.h:
  - SAI_OBJECT_TYPE_ACL_COUNTER
  - SAI_OBJECT_TYPE_ACL_ENTRY
  - SAI_OBJECT_TYPE_ACL_RANGE
  - SAI_OBJECT_TYPE_ACL_TABLE
  - SAI_OBJECT_TYPE_ACL_TABLE_CHAIN_GROUP
  - SAI_OBJECT_TYPE_ACL_TABLE_GROUP
  - SAI_OBJECT_TYPE_ACL_TABLE_GROUP_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiacl_api_attributes.json',
)


class SaiAclTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiacl.h:
        SAI_OBJECT_TYPE_ACL_COUNTER
        SAI_OBJECT_TYPE_ACL_ENTRY
        SAI_OBJECT_TYPE_ACL_RANGE
        SAI_OBJECT_TYPE_ACL_TABLE
        SAI_OBJECT_TYPE_ACL_TABLE_CHAIN_GROUP
        SAI_OBJECT_TYPE_ACL_TABLE_GROUP
        SAI_OBJECT_TYPE_ACL_TABLE_GROUP_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_ACL_COUNTER', 'SAI_OBJECT_TYPE_ACL_ENTRY', 'SAI_OBJECT_TYPE_ACL_RANGE', 'SAI_OBJECT_TYPE_ACL_TABLE', 'SAI_OBJECT_TYPE_ACL_TABLE_CHAIN_GROUP', 'SAI_OBJECT_TYPE_ACL_TABLE_GROUP', 'SAI_OBJECT_TYPE_ACL_TABLE_GROUP_MEMBER']
