"""
Auto-generated PTF test for inc/saineighbor.h.

Validates all SAI object types defined in inc/saineighbor.h:
  - SAI_OBJECT_TYPE_NEIGHBOR_ENTRY

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saineighbor_api_attributes.json',
)


class SaiNeighborTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saineighbor.h:
        SAI_OBJECT_TYPE_NEIGHBOR_ENTRY
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_NEIGHBOR_ENTRY']
