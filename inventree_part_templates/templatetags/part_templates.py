""" 
    Main include file for all template tags and filters for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from inventree_part_templates.version import PLUGIN_VERSION
from .shared import register

# Django won't recognize this as a valid tag library unless we include at least one tag or filter
# directly in this file, so we have a simple tag that returns the version of the plugin.  All other
# tags are in their own files, and use the .shared.register decorator to register them with the library.

@register.simple_tag()
def part_templates_verison() -> str:
    """
    Returns the version of the part templates plugin
    """
    return PLUGIN_VERSION
