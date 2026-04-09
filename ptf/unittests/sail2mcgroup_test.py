"""
Auto-generated PTF test for inc/sail2mcgroup.h.

Validates all SAI object types defined in inc/sail2mcgroup.h:
  - SAI_OBJECT_TYPE_L2MC_GROUP
  - SAI_OBJECT_TYPE_L2MC_GROUP_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'sail2mcgroup_api_attributes.json',
)


class SaiL2mcgroupTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/sail2mcgroup.h:
        SAI_OBJECT_TYPE_L2MC_GROUP
        SAI_OBJECT_TYPE_L2MC_GROUP_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_L2MC_GROUP', 'SAI_OBJECT_TYPE_L2MC_GROUP_MEMBER']
