""" 
    'explore' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from .shared import register
from django.utils.translation import gettext_lazy as _

@register.simple_tag(takes_context=True)
def call(context, obj, method_name, *args):
    """
    Call a method by name on an object with any number of arguments and return the result.

    Example:
    - {% call part "getRequiredParts" true as required_parts %}
    """
    # Process 'as' and the variable name
    if 'as' in args:
        as_index = args.index('as')  # Find the index of 'as'
        if as_index + 1 < len(args):
            varname = args[as_index + 1]  # Get the variable name following 'as'
            args = args[:as_index]  # Remove 'as' and the variable name from args
        else:
            return _("[Call error: Usage of 'as' must be followed by a variable name.")
    else:
        varname = None

    # Call the method
    result = None
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        if callable(method):
            result = method(*args)

    # Assign result to variable in context if varname is provided
    if varname:
        context[varname] = result
        return ''
    return result
