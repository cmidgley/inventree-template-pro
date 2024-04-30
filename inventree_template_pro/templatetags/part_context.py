""" 
    'replace' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from typing import Dict
from inventree_template_pro.property_context import PropertyContext
from inventree_template_pro.constants import TEMPLATETAGS_CONTEXT_PLUGIN
from .shared import register
from django.template import Context
from django.utils.translation import gettext_lazy as _
from inventree_template_pro.constants import CONTEXT_KEY

@register.simple_tag(takes_context=True)
def part_context(context: Context, pk: str) -> Dict[str, str]:
    """
    Takes a primary key for a part (the part ID) and renders the various context templates for the
    part, providing them in a Django context dictionary for access from reports or labels.  Used for
    accessing secondary parts referenced, such as in a report where the report loops through a
    collection of parts and wants to access the context properties for each part.

    Example:
    - {% get_context part.pk as template_context %}
    """
    # make sure we have the plugin in context
    plugin = context.get(TEMPLATETAGS_CONTEXT_PLUGIN)
    if not plugin:
        return { 'error': _("[Internal error: inventree_template_pro unable to locate plugin inside context]") }

    # instantiate the plugin class to so we can get the property context for this part
    property_context = PropertyContext(pk)
    if not property_context.get_part():
        return { 'error': _('[get_context "{pk}": part not found').format(pk=pk) }

    # get the context for this part
    template_context: Dict[str, Dict[str, str]] = {}
    property_context.get_context(template_context, plugin)

    return template_context[CONTEXT_KEY]
