"""
Auto-generated PTF test for inc/saiudf.h.

Validates all SAI object types defined in inc/saiudf.h:
  - SAI_OBJECT_TYPE_UDF
  - SAI_OBJECT_TYPE_UDF_GROUP
  - SAI_OBJECT_TYPE_UDF_MATCH

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiudf_api_attributes.json',
)


class SaiUdfTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiudf.h:
        SAI_OBJECT_TYPE_UDF
        SAI_OBJECT_TYPE_UDF_GROUP
        SAI_OBJECT_TYPE_UDF_MATCH
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_UDF', 'SAI_OBJECT_TYPE_UDF_GROUP', 'SAI_OBJECT_TYPE_UDF_MATCH']
