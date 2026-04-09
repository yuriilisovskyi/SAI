"""
Auto-generated PTF test for inc/saiipmcgroup.h.

Validates all SAI object types defined in inc/saiipmcgroup.h:
  - SAI_OBJECT_TYPE_IPMC_GROUP
  - SAI_OBJECT_TYPE_IPMC_GROUP_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saiipmcgroup_api_attributes.json',
)


class SaiIpmcgroupTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiipmcgroup.h:
        SAI_OBJECT_TYPE_IPMC_GROUP
        SAI_OBJECT_TYPE_IPMC_GROUP_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_IPMC_GROUP', 'SAI_OBJECT_TYPE_IPMC_GROUP_MEMBER']
