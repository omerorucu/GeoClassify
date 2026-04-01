# -*- coding: utf-8 -*-
"""
Resources for GeoClassify Plugin.

Icon and asset paths used across the plugin. Centralised here so that
any path change only needs to be made in one place.

If you want to embed icons as binary data (for distribution without
loose files), compile this module with pyrcc5:

    pyrcc5 resources.qrc -o resources.py

and call ``import resources`` in __init__.py before any QIcon is created.
"""

import os

# Directory that contains this file (the plugin root)
_PLUGIN_DIR = os.path.dirname(__file__)


def plugin_path(*parts):
    """Return an absolute path relative to the plugin root directory.

    Example::

        icon_path = plugin_path('icons', 'my_icon.png')
    """
    return os.path.join(_PLUGIN_DIR, *parts)


# ------------------------------------------------------------------
# Asset paths
# ------------------------------------------------------------------
ICON_PATH        = plugin_path('icon.png')
# Convenience dict – kept for backwards compatibility
resources = {
    'icon': ICON_PATH,
}
