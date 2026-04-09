"""
Auto-generated PTF test for inc/sainat.h.

Validates all SAI object types defined in inc/sainat.h:
  - SAI_OBJECT_TYPE_NAT_ENTRY
  - SAI_OBJECT_TYPE_NAT_ZONE_COUNTER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'sainat_api_attributes.json',
)


class SaiNatTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/sainat.h:
        SAI_OBJECT_TYPE_NAT_ENTRY
        SAI_OBJECT_TYPE_NAT_ZONE_COUNTER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_NAT_ENTRY', 'SAI_OBJECT_TYPE_NAT_ZONE_COUNTER']
