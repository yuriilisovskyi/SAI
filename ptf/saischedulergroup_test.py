"""
Auto-generated PTF test for inc/saischedulergroup.h.

Validates all SAI object types defined in inc/saischedulergroup.h:
  - SAI_OBJECT_TYPE_SCHEDULER_GROUP

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saischedulergroup_api_attributes.json',
)


class SaiSchedulergroupTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saischedulergroup.h:
        SAI_OBJECT_TYPE_SCHEDULER_GROUP
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_SCHEDULER_GROUP']
