import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import parsing
import code_references
import matching
import check_validity
import request_api
import codeislow
import app
