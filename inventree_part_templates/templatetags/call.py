""" 
    'explore' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from .shared import register

@register.simple_tag
def call(obj, method_name, *args):
    """
    Call a method by name on an object with any number of arguments and return the result.

    Example:
    - {% call part "getRequiredParts" true as required_parts %}
    """
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        if callable(method):
            return method(*args)
    return None
