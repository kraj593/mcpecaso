__author__ = 'Kaushik Raj & Naveen Venayak'

import sys
from warnings import warn
from .core import *

if sys.version_info.major < 3:
    warn(Exception('Require Python >= 3.5'))
