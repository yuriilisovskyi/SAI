"""
Auto-generated PTF test for inc/saidtel.h.

Validates all SAI object types defined in inc/saidtel.h:
  - SAI_OBJECT_TYPE_DTEL
  - SAI_OBJECT_TYPE_DTEL_EVENT
  - SAI_OBJECT_TYPE_DTEL_INT_SESSION
  - SAI_OBJECT_TYPE_DTEL_QUEUE_REPORT
  - SAI_OBJECT_TYPE_DTEL_REPORT_SESSION

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saidtel_api_attributes.json',
)


class SaiDtelTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saidtel.h:
        SAI_OBJECT_TYPE_DTEL
        SAI_OBJECT_TYPE_DTEL_EVENT
        SAI_OBJECT_TYPE_DTEL_INT_SESSION
        SAI_OBJECT_TYPE_DTEL_QUEUE_REPORT
        SAI_OBJECT_TYPE_DTEL_REPORT_SESSION
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_DTEL', 'SAI_OBJECT_TYPE_DTEL_EVENT', 'SAI_OBJECT_TYPE_DTEL_INT_SESSION', 'SAI_OBJECT_TYPE_DTEL_QUEUE_REPORT', 'SAI_OBJECT_TYPE_DTEL_REPORT_SESSION']
