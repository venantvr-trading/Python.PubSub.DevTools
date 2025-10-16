#!/usr/bin/env python3
"""
This module is deprecated.

The event scanning logic has been moved to the standalone 'python-pubsub-scanner' library.
This file is kept for historical purposes and will be removed in a future version.
"""

import warnings

warnings.warn(
    "The 'scanner' module is deprecated and will be removed. "
    "Please use the 'python-pubsub-scanner' library instead.",
    DeprecationWarning,
    stacklevel=2
)
