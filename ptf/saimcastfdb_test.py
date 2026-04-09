"""
Auto-generated PTF test for inc/saimcastfdb.h.

Validates all SAI object types defined in inc/saimcastfdb.h:
  - SAI_OBJECT_TYPE_MCAST_FDB_ENTRY

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saimcastfdb_api_attributes.json',
)


class SaiMcastfdbTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saimcastfdb.h:
        SAI_OBJECT_TYPE_MCAST_FDB_ENTRY
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_MCAST_FDB_ENTRY']
