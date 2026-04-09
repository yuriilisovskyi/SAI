"""
Auto-generated PTF test for inc/saitam.h.

Validates all SAI object types defined in inc/saitam.h:
  - SAI_OBJECT_TYPE_TAM
  - SAI_OBJECT_TYPE_TAM_COLLECTOR
  - SAI_OBJECT_TYPE_TAM_COUNTER_SUBSCRIPTION
  - SAI_OBJECT_TYPE_TAM_EVENT
  - SAI_OBJECT_TYPE_TAM_EVENT_ACTION
  - SAI_OBJECT_TYPE_TAM_EVENT_THRESHOLD
  - SAI_OBJECT_TYPE_TAM_INT
  - SAI_OBJECT_TYPE_TAM_MATH_FUNC
  - SAI_OBJECT_TYPE_TAM_REPORT
  - SAI_OBJECT_TYPE_TAM_TELEMETRY
  - SAI_OBJECT_TYPE_TAM_TEL_TYPE
  - SAI_OBJECT_TYPE_TAM_TRANSPORT

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

# ptf/unittests/ → ../../sai_data/<file>
_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sai_data', 'saitam_api_attributes.json',
)


class SaiTamTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saitam.h:
        SAI_OBJECT_TYPE_TAM
        SAI_OBJECT_TYPE_TAM_COLLECTOR
        SAI_OBJECT_TYPE_TAM_COUNTER_SUBSCRIPTION
        SAI_OBJECT_TYPE_TAM_EVENT
        SAI_OBJECT_TYPE_TAM_EVENT_ACTION
        SAI_OBJECT_TYPE_TAM_EVENT_THRESHOLD
        SAI_OBJECT_TYPE_TAM_INT
        SAI_OBJECT_TYPE_TAM_MATH_FUNC
        SAI_OBJECT_TYPE_TAM_REPORT
        SAI_OBJECT_TYPE_TAM_TELEMETRY
        SAI_OBJECT_TYPE_TAM_TEL_TYPE
        SAI_OBJECT_TYPE_TAM_TRANSPORT
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_TAM', 'SAI_OBJECT_TYPE_TAM_COLLECTOR', 'SAI_OBJECT_TYPE_TAM_COUNTER_SUBSCRIPTION', 'SAI_OBJECT_TYPE_TAM_EVENT', 'SAI_OBJECT_TYPE_TAM_EVENT_ACTION', 'SAI_OBJECT_TYPE_TAM_EVENT_THRESHOLD', 'SAI_OBJECT_TYPE_TAM_INT', 'SAI_OBJECT_TYPE_TAM_MATH_FUNC', 'SAI_OBJECT_TYPE_TAM_REPORT', 'SAI_OBJECT_TYPE_TAM_TELEMETRY', 'SAI_OBJECT_TYPE_TAM_TEL_TYPE', 'SAI_OBJECT_TYPE_TAM_TRANSPORT']
