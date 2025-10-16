#!/usr/bin/env python3
"""
This module is deprecated.

The event analysis logic has been moved to the standalone 'python-pubsub-scanner' library.
This file is kept for historical purposes and will be removed in a future version.
"""

import warnings

warnings.warn(
    "The 'analyze_event_flow' module is deprecated and will be removed. "
    "Its logic is now part of the 'python-pubsub-scanner' library.",
    DeprecationWarning,
    stacklevel=2
)
