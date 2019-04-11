__author__ = 'Kaushik Raj & Naveen Venayak'

import sys
from warnings import warn

if sys.version_info.major < 3:
    warn(Exception('Require Python >= 3.5'))

from .core import *

