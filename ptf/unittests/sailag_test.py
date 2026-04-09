"""
Auto-generated PTF test for inc/sailag.h.

Validates all SAI object types defined in inc/sailag.h:
  - SAI_OBJECT_TYPE_LAG
  - SAI_OBJECT_TYPE_LAG_MEMBER

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'sailag_api_attributes.json',
)


class SaiLagTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/sailag.h:
        SAI_OBJECT_TYPE_LAG
        SAI_OBJECT_TYPE_LAG_MEMBER
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_LAG', 'SAI_OBJECT_TYPE_LAG_MEMBER']
