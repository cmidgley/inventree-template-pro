""" 
    'explore' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from __future__ import annotations


from typing import Any, Dict
from django.utils.safestring import mark_safe
from django.template import Context
from django.utils.translation import gettext_lazy as _
from inventree_template_pro.templatetags.inspect import InspectionManager
from .shared import register

@register.simple_tag(takes_context=True)
def explore(context: Context, obj:Any, depth=3, lists=5, methods=False, privates=False, style="list", none=True) -> str:
    """
    Tag to explore properties of an object for finding and understanding properties
    on various objects.

    If you specify a single numeric option, it will be used as the depth (the maximum recursion
    depth to explore the object).  For example:

    `{% explore part 5 }}`

    If you want to specify additional options, use named arguments such as:

    `{% explore part depth=5 methods=True privates=True lists=50 style="interactive" }}`

    This will show the first 5 levels of the object, show methods, show private/protected
    members, and show up to the first 50 lines of lists.  It also switches to the "interactive"
    style (see templates/template_pro/inspect/* for the styles and templates).

    Options are:
    - depth=<number>: set the maximum depth to explore (default 3).
    - lists=<number>: set the maximum number of items in a list to include (default 5).
    - methods=True/False: if methods and partials are included in the output (default False).
    - privates=True/False: if private and protected members (_ and __) are included in the output
    (default False).
    - style=<style>: set the output style (template) to use (default "list").
    - none: if properties that resolve to None are included in the output (default True).

    Example:
    - {% explore my_object %}
    - {% explore part.category 5 %}
    - {% explore part lists=10 %}
    - {% explore part depth=5 methods %}
    """
    # set up the options dictionary
    manager_options: Dict[str, str|int|bool] = {
        'depth': depth, 
        'methods': methods, 
        'privates': privates, 
        'lists': lists, 
        'style': style,
        'none': none
    }

    # explore the object
    formatted_html = InspectionManager("Explore", obj, manager_options, context).format()
    return mark_safe(formatted_html)
