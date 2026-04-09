"""
Auto-generated PTF test for inc/saisrv6.h.

Validates all SAI object types defined in inc/saisrv6.h:
  - SAI_OBJECT_TYPE_MY_SID_ENTRY
  - SAI_OBJECT_TYPE_SRV6_SIDLIST

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saisrv6_api_attributes.json',
)


class SaiSrv6Test(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saisrv6.h:
        SAI_OBJECT_TYPE_MY_SID_ENTRY
        SAI_OBJECT_TYPE_SRV6_SIDLIST
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_MY_SID_ENTRY', 'SAI_OBJECT_TYPE_SRV6_SIDLIST']
