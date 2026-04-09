"""
Auto-generated PTF test for inc/saihash.h.

Validates all SAI object types defined in inc/saihash.h:
  - SAI_OBJECT_TYPE_FINE_GRAINED_HASH_FIELD
  - SAI_OBJECT_TYPE_HASH

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saihash_api_attributes.json',
)


class SaiHashTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saihash.h:
        SAI_OBJECT_TYPE_FINE_GRAINED_HASH_FIELD
        SAI_OBJECT_TYPE_HASH
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_FINE_GRAINED_HASH_FIELD', 'SAI_OBJECT_TYPE_HASH']
