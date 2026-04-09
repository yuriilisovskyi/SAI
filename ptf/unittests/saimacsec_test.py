"""
Auto-generated PTF test for inc/saimacsec.h.

Validates all SAI object types defined in inc/saimacsec.h:
  - SAI_OBJECT_TYPE_MACSEC
  - SAI_OBJECT_TYPE_MACSEC_FLOW
  - SAI_OBJECT_TYPE_MACSEC_PORT
  - SAI_OBJECT_TYPE_MACSEC_SA
  - SAI_OBJECT_TYPE_MACSEC_SC

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saimacsec_api_attributes.json',
)


class SaiMacsecTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saimacsec.h:
        SAI_OBJECT_TYPE_MACSEC
        SAI_OBJECT_TYPE_MACSEC_FLOW
        SAI_OBJECT_TYPE_MACSEC_PORT
        SAI_OBJECT_TYPE_MACSEC_SA
        SAI_OBJECT_TYPE_MACSEC_SC
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_MACSEC', 'SAI_OBJECT_TYPE_MACSEC_FLOW', 'SAI_OBJECT_TYPE_MACSEC_PORT', 'SAI_OBJECT_TYPE_MACSEC_SA', 'SAI_OBJECT_TYPE_MACSEC_SC']
