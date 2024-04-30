""" 
    Main include file for all template tags and filters for the inventree-template-pro plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from inventree_template_pro.version import PLUGIN_VERSION
from .shared import register

# Django won't recognize this as a valid tag library unless we include at least one tag or filter
# directly in this file, so we have a simple tag that returns the version of the plugin.  All other
# tags are in their own files, and use the .shared.register decorator to register them with the library.

@register.simple_tag()
def template_pro_verison() -> str:
    """
    Returns the version of the part templates plugin
    """
    return PLUGIN_VERSION
