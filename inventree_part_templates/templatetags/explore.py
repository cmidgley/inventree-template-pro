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
from inventree_part_templates.templatetags.inspect import InspectionManager
from .shared import register

@register.simple_tag(takes_context=True)
def explore(context: Context, obj:Any, depth=3, lists=5, methods=False, privates=False, style="list") -> str:
    """
    Tag to explore properties of an object for finding and understanding properties
    on various objects.  By default shows the first three levels of the object, limits 
    limits to 5 items, does not show private/protected members, and does not show 
    methods/partials.  It also uses the default output style (template) of 'list'.
    All of these can be controlled with options.

    If you specify a single numeric option, it will be used as the depth:

    `{% explore part 5 }}`

    If you want to specify additional options, use named arguments such as:

    `{% explore part depth=5 methods=True privates=True lists=50 style="interactive" }}`

    This will show the first 5 levels of the object, show methods, show private/protected
    members, and show up to the first 50 lines of lists.  It also switches to the "interactive"
    style (see templates/part_templates/inspect/* for the styles and templates).

    Options are:
    - depth=<number>: set the maximum depth to explore.
    - lists=<number>: set the maximum number of items in a list to include.
    - methods: include methods and partials in the output.
    - privates: include private and protected members in the output.
    - style=<style>: set the output style (template) to use.  The default is "list".

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
        'style': style 
    }

    # explore the object
    formatted_html = InspectionManager("Explore", obj, manager_options, context).format()
    return mark_safe(formatted_html)
