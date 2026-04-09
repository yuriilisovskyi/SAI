"""
Auto-generated PTF test for inc/sainexthopgroup.h.

Validates all SAI object types defined in inc/sainexthopgroup.h:
  - SAI_OBJECT_TYPE_NEXT_HOP_GROUP
  - SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MAP
  - SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'sainexthopgroup_api_attributes.json',
)


class SaiNexthopgroupTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/sainexthopgroup.h:
        SAI_OBJECT_TYPE_NEXT_HOP_GROUP
        SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MAP
        SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_NEXT_HOP_GROUP', 'SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MAP', 'SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER']
