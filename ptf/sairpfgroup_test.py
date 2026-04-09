"""
Auto-generated PTF test for inc/sairpfgroup.h.

Validates all SAI object types defined in inc/sairpfgroup.h:
  - SAI_OBJECT_TYPE_RPF_GROUP
  - SAI_OBJECT_TYPE_RPF_GROUP_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'sairpfgroup_api_attributes.json',
)


class SaiRpfgroupTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/sairpfgroup.h:
        SAI_OBJECT_TYPE_RPF_GROUP
        SAI_OBJECT_TYPE_RPF_GROUP_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_RPF_GROUP', 'SAI_OBJECT_TYPE_RPF_GROUP_MEMBER']
