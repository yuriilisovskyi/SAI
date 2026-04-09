"""
Auto-generated PTF test for inc/saiisolationgroup.h.

Validates all SAI object types defined in inc/saiisolationgroup.h:
  - SAI_OBJECT_TYPE_ISOLATION_GROUP
  - SAI_OBJECT_TYPE_ISOLATION_GROUP_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiisolationgroup_api_attributes.json',
)


class SaiIsolationgroupTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiisolationgroup.h:
        SAI_OBJECT_TYPE_ISOLATION_GROUP
        SAI_OBJECT_TYPE_ISOLATION_GROUP_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_ISOLATION_GROUP', 'SAI_OBJECT_TYPE_ISOLATION_GROUP_MEMBER']
