"""
Auto-generated PTF test for inc/saibuffer.h.

Validates all SAI object types defined in inc/saibuffer.h:
  - SAI_OBJECT_TYPE_BUFFER_POOL
  - SAI_OBJECT_TYPE_BUFFER_PROFILE
  - SAI_OBJECT_TYPE_INGRESS_PRIORITY_GROUP

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saibuffer_api_attributes.json',
)


class SaiBufferTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saibuffer.h:
        SAI_OBJECT_TYPE_BUFFER_POOL
        SAI_OBJECT_TYPE_BUFFER_PROFILE
        SAI_OBJECT_TYPE_INGRESS_PRIORITY_GROUP
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_BUFFER_POOL', 'SAI_OBJECT_TYPE_BUFFER_PROFILE', 'SAI_OBJECT_TYPE_INGRESS_PRIORITY_GROUP']
