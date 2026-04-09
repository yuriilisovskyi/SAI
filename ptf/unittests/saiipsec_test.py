"""
Auto-generated PTF test for inc/saiipsec.h.

Validates all SAI object types defined in inc/saiipsec.h:
  - SAI_OBJECT_TYPE_IPSEC
  - SAI_OBJECT_TYPE_IPSEC_PORT
  - SAI_OBJECT_TYPE_IPSEC_SA

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saiipsec_api_attributes.json',
)


class SaiIpsecTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiipsec.h:
        SAI_OBJECT_TYPE_IPSEC
        SAI_OBJECT_TYPE_IPSEC_PORT
        SAI_OBJECT_TYPE_IPSEC_SA
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_IPSEC', 'SAI_OBJECT_TYPE_IPSEC_PORT', 'SAI_OBJECT_TYPE_IPSEC_SA']
