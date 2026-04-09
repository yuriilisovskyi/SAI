"""
Auto-generated PTF test for inc/saiport.h.

Validates all SAI object types defined in inc/saiport.h:
  - SAI_OBJECT_TYPE_PORT
  - SAI_OBJECT_TYPE_PORT_CONNECTOR
  - SAI_OBJECT_TYPE_PORT_POOL
  - SAI_OBJECT_TYPE_PORT_SERDES

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiport_api_attributes.json',
)


class SaiPortTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiport.h:
        SAI_OBJECT_TYPE_PORT
        SAI_OBJECT_TYPE_PORT_CONNECTOR
        SAI_OBJECT_TYPE_PORT_POOL
        SAI_OBJECT_TYPE_PORT_SERDES
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_PORT', 'SAI_OBJECT_TYPE_PORT_CONNECTOR', 'SAI_OBJECT_TYPE_PORT_POOL', 'SAI_OBJECT_TYPE_PORT_SERDES']
