"""
Auto-generated PTF test for inc/saiswitch.h.

Validates all SAI object types defined in inc/saiswitch.h:
  - SAI_OBJECT_TYPE_SWITCH
  - SAI_OBJECT_TYPE_SWITCH_TUNNEL

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiswitch_api_attributes.json',
)


class SaiSwitchTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiswitch.h:
        SAI_OBJECT_TYPE_SWITCH
        SAI_OBJECT_TYPE_SWITCH_TUNNEL
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_SWITCH', 'SAI_OBJECT_TYPE_SWITCH_TUNNEL']
