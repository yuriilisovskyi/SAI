"""
Auto-generated PTF test for inc/saivlan.h.

Validates all SAI object types defined in inc/saivlan.h:
  - SAI_OBJECT_TYPE_VLAN
  - SAI_OBJECT_TYPE_VLAN_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saivlan_api_attributes.json',
)


class SaiVlanTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saivlan.h:
        SAI_OBJECT_TYPE_VLAN
        SAI_OBJECT_TYPE_VLAN_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_VLAN', 'SAI_OBJECT_TYPE_VLAN_MEMBER']
