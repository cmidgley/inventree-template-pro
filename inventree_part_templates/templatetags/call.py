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
            # result = method(*args)
            result = getRequiredParts(obj, recursive=True, parts=None)
    varname = kwargs.get('as')
    if varname:
        context[varname] = result
        return ''
    return result

def getRequiredParts(part, recursive=False, parts=None):
    if parts is None:
        parts = set()

    bom_items = part.get_bom_items()

    for bom_item in bom_items:
        sub_part = bom_item.sub_part

        if sub_part not in parts:
            parts.add(sub_part)

            if recursive:
                sub_part.getRequiredParts(part, recursive=True, parts=parts)

    return parts
