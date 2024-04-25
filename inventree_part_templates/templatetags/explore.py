""" 
    'explore' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from __future__ import annotations


from typing import Any, Dict
from django.utils.safestring import mark_safe
from inventree_part_templates.templatetags.inspect import InspectionManager
from .shared import register
from django.utils.translation import gettext_lazy as _

@register.filter()
def explore(obj:Any, options=None) -> str:
    """
    Filter to explore properties of an object for finding and understanding properties
    on various objects.  By default shows the first three levels of the object, limits 
    limits to 5 items, does not show private/protected members, and does not show 
    methods/partials.  It also uses the default output style (template) of 'list'.
    All of these can be controlled with options.

    If you specify a single numeric option, it will be used as the depth:

    `{{ part|explore:5 }}`

    If you want to specify additional options, use a string with options separated by
    commas:

    `{{ part|explore:"depth=5,methods,privates,lists=50,style=interactive" }}`

    This will show the first 5 levels of the object, show methods, show private/protected
    members, and show up to the first 50 lines of lists.  It also switches to the "interactive"
    style (see templates/part_templates/inspect/* for the styles and templates).

    Options are:
    - depth=<number>: set the maximum depth to explore.
    - lists=<number>: set the maximum number of items in a list to include.
    - methods: include methods and partials in the output.
    - privates: include private and protected members in the output.
    - style=<style>: set the output style (template) to use.  The default is 'list'.

    Example:
    - part|explore:3
    - part|explore:"lists=10"
    - part|explore:"depth=5,methods"
    """
    # decode the options into a dictionary
    manager_options: Dict[str, str|int|bool] = { 'depth': 3, 'methods': False, 'privates': False, 'lists': 5, 'style': 'list' }
    if options is not None:
        if isinstance(options, str):
            # Split the string by commas
            split_options = options.split(',')
            
            # decode each option
            for split_option in split_options:
                if '=' in split_option:
                    key, value = split_option.split('=')
                    if (key in ('depth', 'lists')) and (value.isdigit()):
                        manager_options[key.strip().lower()] = int(value.strip())
                    elif key in ('style'):
                        manager_options[key.strip().lower()] = value.strip().lower()
                    else:
                        raise ValueError(_("Unknown option: ") + split_option)
                else:
                    if split_option in ('methods', 'privates'):
                        manager_options[key.strip().lower()] = True
                    else:
                        raise ValueError(_("Unknown option: ") + split_option)
        else:
            try:
                manager_options['depth'] = int(options)
            except ValueError:
                pass

    # explore the object
    formatted_html = InspectionManager("Explore", obj, manager_options).format()
    return mark_safe(formatted_html)
