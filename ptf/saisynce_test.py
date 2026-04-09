"""
Auto-generated PTF test for inc/saisynce.h.

Validates all SAI object types defined in inc/saisynce.h:
  - SAI_OBJECT_TYPE_SYNCE_CLOCK

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saisynce_api_attributes.json',
)


class SaiSynceTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saisynce.h:
        SAI_OBJECT_TYPE_SYNCE_CLOCK
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_SYNCE_CLOCK']
