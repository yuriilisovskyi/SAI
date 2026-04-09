"""
Auto-generated PTF test for inc/saihostif.h.

Validates all SAI object types defined in inc/saihostif.h:
  - SAI_OBJECT_TYPE_HOSTIF
  - SAI_OBJECT_TYPE_HOSTIF_PACKET
  - SAI_OBJECT_TYPE_HOSTIF_TABLE_ENTRY
  - SAI_OBJECT_TYPE_HOSTIF_TRAP
  - SAI_OBJECT_TYPE_HOSTIF_TRAP_GROUP
  - SAI_OBJECT_TYPE_HOSTIF_USER_DEFINED_TRAP

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saihostif_api_attributes.json',
)


class SaiHostifTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saihostif.h:
        SAI_OBJECT_TYPE_HOSTIF
        SAI_OBJECT_TYPE_HOSTIF_PACKET
        SAI_OBJECT_TYPE_HOSTIF_TABLE_ENTRY
        SAI_OBJECT_TYPE_HOSTIF_TRAP
        SAI_OBJECT_TYPE_HOSTIF_TRAP_GROUP
        SAI_OBJECT_TYPE_HOSTIF_USER_DEFINED_TRAP
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_HOSTIF', 'SAI_OBJECT_TYPE_HOSTIF_PACKET', 'SAI_OBJECT_TYPE_HOSTIF_TABLE_ENTRY', 'SAI_OBJECT_TYPE_HOSTIF_TRAP', 'SAI_OBJECT_TYPE_HOSTIF_TRAP_GROUP', 'SAI_OBJECT_TYPE_HOSTIF_USER_DEFINED_TRAP']
