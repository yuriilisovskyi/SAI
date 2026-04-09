"""
Auto-generated PTF test for inc/sail2mc.h.

Validates all SAI object types defined in inc/sail2mc.h:
  - SAI_OBJECT_TYPE_L2MC_ENTRY

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'sail2mc_api_attributes.json',
)


class SaiL2mcTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/sail2mc.h:
        SAI_OBJECT_TYPE_L2MC_ENTRY
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_L2MC_ENTRY']
