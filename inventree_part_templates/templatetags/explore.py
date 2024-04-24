""" 
    'explore' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from __future__ import annotations


from typing import Dict, Any
from django.utils.safestring import mark_safe
from django import template
from django.utils.translation import gettext_lazy as _
from inventree_part_templates.templatetags.inspect import InspectionManager

# define register so that Django can find the tags/filters
register = template.Library()
    
@register.filter()
def explore(obj:Any, depth='2') -> str:
    """
    Filter to explore properties of an object for finding and understanding properties
    on various objects.  By default shows the first two levels of the object, but the
    parameter can specify a specific depth.  While attempts are made to avoid recursion
    (objects that point eventually back to themselves), not all objects work with this so
    very large depths can create massive output or even a stack overflow.

    Example:
    - part|explore:3    
    """
    # decode the options
    try:
        int_depth = int(depth)
    except ValueError:
        int_depth = 2

    # explore the object
    formatted_html = InspectionManager("Explore", obj, int_depth).format()
    return mark_safe(formatted_html)
