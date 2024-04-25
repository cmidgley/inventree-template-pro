""" 
    'explore' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from __future__ import annotations


from typing import Any
from django.utils.safestring import mark_safe
from inventree_part_templates.templatetags.inspect import InspectionManager
from .shared import register
from django.utils.translation import gettext_lazy as _

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
    formatted_html = InspectionManager("Explore", obj, int_depth).format('interactive')
    return mark_safe(formatted_html)
