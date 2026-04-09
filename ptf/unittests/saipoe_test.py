"""
Auto-generated PTF test for inc/saipoe.h.

Validates all SAI object types defined in inc/saipoe.h:
  - SAI_OBJECT_TYPE_POE_DEVICE
  - SAI_OBJECT_TYPE_POE_PORT
  - SAI_OBJECT_TYPE_POE_PSE

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saipoe_api_attributes.json',
)


class SaiPoeTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saipoe.h:
        SAI_OBJECT_TYPE_POE_DEVICE
        SAI_OBJECT_TYPE_POE_PORT
        SAI_OBJECT_TYPE_POE_PSE
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_POE_DEVICE', 'SAI_OBJECT_TYPE_POE_PORT', 'SAI_OBJECT_TYPE_POE_PSE']
