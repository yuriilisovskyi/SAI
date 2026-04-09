"""
Auto-generated PTF test for inc/saiqueue.h.

Validates all SAI object types defined in inc/saiqueue.h:
  - SAI_OBJECT_TYPE_QUEUE

Re-generate by running: python3 generate_sai_json.py
"""

import os
from sai_api_test import SaiApiTestBase

_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'sai_data', 'saiqueue_api_attributes.json',
)


class SaiQueueTest(SaiApiTestBase):
    """
    Exercises all Thrift functions for the following object types
    defined in inc/saiqueue.h:
        SAI_OBJECT_TYPE_QUEUE
    """

    json_path = _JSON
    object_types = ['SAI_OBJECT_TYPE_QUEUE']
