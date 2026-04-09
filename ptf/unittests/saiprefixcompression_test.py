"""
Auto-generated PTF test for inc/saiprefixcompression.h.

Validates all SAI object types defined in inc/saiprefixcompression.h:
  - SAI_OBJECT_TYPE_PREFIX_COMPRESSION_ENTRY
  - SAI_OBJECT_TYPE_PREFIX_COMPRESSION_TABLE

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiprefixcompression_api_attributes.json',
)


class SaiPrefixcompressionTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiprefixcompression.h:
        SAI_OBJECT_TYPE_PREFIX_COMPRESSION_ENTRY
        SAI_OBJECT_TYPE_PREFIX_COMPRESSION_TABLE
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_PREFIX_COMPRESSION_ENTRY', 'SAI_OBJECT_TYPE_PREFIX_COMPRESSION_TABLE']
