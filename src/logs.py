#!/usr/bin/env python3.8

import os
# import sys
# import logging
# import functools
from datetime import datetime, timezone
    
log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs")

def logger(fn):
    
    def inner(*args, **kwargs):
        called_at = datetime.now(timezone.utc)
        to_execute = fn(*args, **kwargs)
        
        print('{0} executed. Logged at {1}. Resultats {2}'.format(fn.__name__, called_at, to_execute))
        return to_execute
    
    return inner