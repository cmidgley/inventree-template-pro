""" 
    Main include file for all template tags and filters for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from inventree_part_templates.version import PLUGIN_VERSION
from .shared import register
from .explore import explore
from .replace import replace
from .stocklist import stocklist
from .value_filters import scrub, value, item
from .part_context import part_context

__all__ = ['explore', 'replace', 'stocklist', 'scrub', 'value', 'item', 'part_context']

@register.simple_tag()
def part_templates_verison() -> str:
    """
    Returns the version of the part templates plugin
    """
    return PLUGIN_VERSION
