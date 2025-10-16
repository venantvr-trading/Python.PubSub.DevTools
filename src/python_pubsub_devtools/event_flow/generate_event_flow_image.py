#!/usr/bin/env python3
"""
This module is deprecated.

The logic for generating static images has been superseded by the interactive SVG graphs
generated via Graphviz/pydot in the web interface.

This file is kept for historical purposes and will be removed in a future version.
"""

import warnings

warnings.warn(
    "The 'generate_event_flow_image' module is deprecated and will be removed. "
    "Graph generation is now handled by the web components.",
    DeprecationWarning,
    stacklevel=2
)
