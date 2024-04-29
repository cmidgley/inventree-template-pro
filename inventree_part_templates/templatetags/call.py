""" 
    'explore' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from .shared import register

@register.simple_tag(takes_context=True)
def call(context, obj, method_name, *args, **kwargs):
    """
    Call a method by name on an object with any number of arguments and return the result.

    Example:
    - {% call part "getRequiredParts" true as required_parts %}
    """
    result = None
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        if callable(method):
            result = method(*args)
    varname = kwargs.get('as')
    if varname:
        context[varname] = result
        return ''
    return result
