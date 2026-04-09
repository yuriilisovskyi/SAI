"""
Auto-generated PTF test for inc/saitunnel.h.

Validates all SAI object types defined in inc/saitunnel.h:
  - SAI_OBJECT_TYPE_TUNNEL
  - SAI_OBJECT_TYPE_TUNNEL_MAP
  - SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY
  - SAI_OBJECT_TYPE_TUNNEL_TERM_TABLE_ENTRY

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saitunnel_api_attributes.json',
)


class SaiTunnelTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saitunnel.h:
        SAI_OBJECT_TYPE_TUNNEL
        SAI_OBJECT_TYPE_TUNNEL_MAP
        SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY
        SAI_OBJECT_TYPE_TUNNEL_TERM_TABLE_ENTRY
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_TUNNEL', 'SAI_OBJECT_TYPE_TUNNEL_MAP', 'SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY', 'SAI_OBJECT_TYPE_TUNNEL_TERM_TABLE_ENTRY']
