"""
Auto-generated PTF test for inc/saiarsprofile.h.

Validates all SAI object types defined in inc/saiarsprofile.h:
  - SAI_OBJECT_TYPE_ARS_PROFILE

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saiarsprofile_api_attributes.json',
)


class SaiArsprofileTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiarsprofile.h:
        SAI_OBJECT_TYPE_ARS_PROFILE
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_ARS_PROFILE']
