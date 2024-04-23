""" 
    Custom Django template tags for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

# for regex
import re

# for html formatting and safety
import html
from django.utils.safestring import mark_safe

# imports to blacklist difficult objects for dumping
import decimal

# for inspecting objects during recursive dump
import inspect

# for reading YAML config file
import os
import yaml
from pathlib import Path

# to add Django filters / tags
from django import template
from django.template import Context

# for accessing the InvenTree models
from part.models import Part
from stock.models import StockItem
from stock.models import StockLocation

# translation support
from django.utils.translation import gettext_lazy as _

# caching of the YAML data
from django.core.cache import cache

# type hinting
from typing import Dict, List, Any

# class to manage the property context
from inventree_part_templates.property_context import PropertyContext

# constants
from inventree_part_templates.constants import TEMPLATETAGS_CONTEXT_PLUGIN

# for explore to dive deeper into queries
from django.db.models.query import QuerySet

# stock items for parts
from stock.models import StockItem

# set how long we cache the config data (in seconds), to allow users to edit it without restarting the server
CACHE_TIMEOUT = 3

# define the types for the yaml config file
FilterRule = Dict[str, str]
FilterRules = List[FilterRule]
Filters = Dict[str, FilterRules]
Config = Dict[str, Filters]

# define register so that Django can find the tags/filters
register = template.Library()


def load_filters() -> Config:
    """
    Provides the filters from the configuration file, from cache or by loading the file.  The file
    path and name can be defined in the environment variable PART_TEMPLATES_CONFIG_FILE, or it will
    default to 'part_templates.yaml' in the inventree-part-templates plugin directory.

    Returns:
        Config: The loaded filters from the configuration file.
    """
    # do we have config cached?
    filters: Config | None = cache.get('part-templates-yaml')
    if not filters:
        # set the path to the config file using environment variable PART_TEPLATES_CONFIG_FILE, or
        # get from the plugin directory if not set
        cfg_filename = os.getenv('PART_TEMPLATES_CONFIG_FILE')
        if cfg_filename:
            cfg_filename = Path(cfg_filename.strip()).resolve()
        else:
            cfg_filename = Path(__file__).parent.parent.joinpath('part_templates.yaml').resolve()

        # load the config file
        with open(cfg_filename, 'r', encoding='utf-8') as file:
            loaded_data = yaml.safe_load(file)
            if (loaded_data is None) or (not isinstance(loaded_data, dict)):
                raise FileNotFoundError(_("File found but contents missing or not dictionary: {cfg_filename}").format(cfg_filename=cfg_filename))
            filters = loaded_data

        # cache the config data
        cache.set('part-templates-yaml', filters, timeout=CACHE_TIMEOUT)
    return filters

@register.simple_tag(takes_context=True)
def get_context(context: Context, pk: str) -> Dict[str, str]:
    """
    Takes a primary key for a part (the part ID) and renders the various context templates for the
    part, providing them in a Django context dictionary for access from reports or labels.  Used for
    accessing secondary parts referenced, such as in a report where the report loops through a
    collection of parts and wants to access the context properties for each part.

    Args:
        context (Context): Context from `takes_context=True`, to get the plugin `SettingsMixin`
        pk (str): The primary key of the part.

    Returns:
        Dict[str, str]: The context for the part properties.
    """
    # make sure we have the plugin in context
    plugin = context.get(TEMPLATETAGS_CONTEXT_PLUGIN)
    if not plugin:
        return { 'error': _("[Internal error: inventree_part_templates unable to locate plugin inside context]") }

    # instantiate the plugin class to so we can get the property context for this part
    property_context = PropertyContext(pk)
    if not property_context.get_part():
        return { 'error': _('[get_context "{pk}": part not found').format(pk=pk) }

    # get the context for this part
    template_context: Dict[str, str] = {}
    property_context.get_context(template_context, plugin)

    return template_context

@register.filter()
def scrub(scrub_string: str, name: str) -> str:
    """
    Scrubs a string (typically from a part parameter) using rules defined in the part_templates.yaml
    file based on the supplied name.  The rules are defined in the configuration file as a list of
    dictionaries, where each dictionary contains a pattern and replacement key using regex.

    Args:
        scrub_string (str): The value to be scrubbed.
        name (str): The name of the filter set in `part_templates.yaml` to be applied.

    Returns:
        str: The scrubbed value.

    Raises:
        FileNotFoundError: If the configuration file is not found.
        yaml.YAMLError: If there is an error in the configuration file.
        re.error: If there is a regex error while applying the rule.

    """
    if not name:
        return _('[scrub missing required :name]')

    try:
        config = load_filters()
    except FileNotFoundError as error:
        return (_('["part_templates.yaml" not found or invalid: {error}]').format(error=str(error)))
    except yaml.YAMLError as error:
        return (_("[Error in configuration file: {error}]").format(error=str(error)))

    filters = config.get('filters')
    if filters is None:
        return _('["filters" not found in "parts_templates.yaml"]')

    # see if we have a set of rules for this key
    rules = filters.get(name)
    if not rules is None:
        # process all rules for this specific key
        for rule in rules:
            pattern = rule.get('pattern')
            if pattern is None:
                return _('["pattern" not found in "{name}" in "parts_templates.yaml"]').format(name=name)
            replacement = rule.get('replacement')
            if replacement is None:
                return _('["replacement" not found in "{name}" in "parts_templates.yaml"]').format(name=name)

            try:
                scrub_string = re.sub(pattern, replacement, scrub_string)
            except re.error as error:
                return _('["{name}" regex error on {pattern}: {error}]').format(name=name, pattern=pattern, error=str(error))

        # see if we have a _GLOBAL rule set
        global_rules = filters.get('_GLOBAL')
        if global_rules is not None:
            for rule in global_rules:
                pattern = rule.get('pattern')
                if pattern is None:
                    return _('["pattern" not found in "_GLOBAL" in "parts_templates.yaml"]')
                replacement = rule.get('replacement')
                if replacement is None:
                    return _('["replacement" not found in "_GLOBAL" in "parts_templates.yaml"]')

                try:
                    scrub_string = re.sub(pattern, replacement, scrub_string)
                except re.error as error:
                    return _('["_GLOBAL regex error on {pattern}: {error}]').format(pattern=pattern, error=str(error))

    return scrub_string

@register.filter()
def value(properties: Dict[str, str], key: str) -> str | None:
    """
    Access to value of a dictionary by key (no scrubbing)

    Example:
    - {% parameters|value:"Rated Voltage" %}
    """
    try:
        return properties.get(key)
    except Exception:       # pylint: disable=broad-except
        return ""

@register.filter()
def item(properties: Dict[str, str], key: str) -> str | None:
    """
    Access to value of a dictionary by key (with scrubbing)

    Example:
    - {% parameters|item:"Package Type" %}
    """
    try:
        item_value = properties.get(key)
    except Exception:       # pylint: disable=broad-except
        return ""

    if item_value:
        return scrub(item_value, key)
    return ""

@register.filter()
def replace(source: str, arg: str):
    """
    Replaces a string value with another, with the filter parameter having two values (match and replace) 
    being separated by the "|" character.  If the "match" side starts with "regex:" then the match and replace
    are processed as regular expressions.  The "|" can be escaped with "\\\\|" if it is needed as a character
    in the string.  

    Examples that all add a space following a separator character:
    - {% "a,b,c"|substitute:",|, " %}
    - {% "A|B|C"|substitute:"\\\\||\\\\|, " %}
    - {% ",\\\\s*(?![,])|, " %}
    """

    # Handle escaped pipe characters and split the arguments
    parts = re.split(r'(?<!\\)\|', arg)
    parts = [part.replace('\\|', '|') for part in parts]

    if len(parts) != 2:
        return _('[replace:"{arg}" must have two parameters separated by "|"]').format(arg=html.escape(arg))

    if parts[0].startswith('regex:'):
        # Regex replacement
        pattern = parts[0][6:]
        repl = parts[1]
        return re.sub(pattern, repl, source)

    # Simple replacement
    match = parts[0]
    repl = parts[1]
    return source.replace(match, repl)

def _track_recursion(obj: Any, processed: Dict[int, bool]) -> bool:
    """
    Check if an object has been processed and add it to the processed dictionary if not.  

    Args:
        obj (Any): The object to check.
        processed (Dict[int, bool]): A dictionary to store processed objects.

    Returns:
        bool: True if the object was not processed before, False if it was already processed.
    """
    obj_id = id(obj)

    if obj_id in processed:
        return False
    processed[obj_id] = True
    return True

# some types are not appropriate for recursive formatting.  They can be added to the blacklist here
# which will simply get their str(obj) value
BLACKLISTED_TYPES = (
    decimal.Decimal,
    complex,
    re.Pattern,
    re.Match,
)


def _format_object(obj: Any, depth: int, processed: Dict[int, bool], level: int = 0) -> str:
    """
    Recursively format an object into HTML with a given depth.
    
    Args:
        obj: The object to format.
        depth (int): The maximum depth to format.
        processed (Dict[int, bool]): Dictionary to look for recursion (reuse of objects)
        level (int): The current level of recursion.
    """
    try:
        single_indent = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        indent = single_indent * level

        # simple types are displayed directly.
        if obj is None:
            return 'None'
        if isinstance(obj, str):
            return f'"{html.escape(str(obj))}" ({type(obj).__name__})'
        if isinstance(obj, (str, int, float, bool, BLACKLISTED_TYPES)) or obj is None:
            return f'{html.escape(str(obj))} ({type(obj).__name__})'

        # make sure we have not recursed on this object before
        if _track_recursion(obj, processed):
            # handle dictionaries by recursing into key-value pairs.
            if isinstance(obj, dict):
                if depth > 0:
                    items = [f"{indent}{single_indent}<span style='font-weight: bold'>'{key}'</span>: {_format_object(value, depth - 1, processed, level + 1)}"
                        for key, value in obj.items()]
                    if len(items) == 0:
                        return '{ }'
                    return '{<br>' + '<br>'.join(items) + f'<br>{indent}}}'
                return "{ ... }"

            # handle lists and tuples by recursing into each element.
            if isinstance(obj, (list, tuple)):
                if depth > 0:
                    items = [
                            f"{indent}{single_indent}{index}: {_format_object(item, depth - 1, processed, level + 1)}"
                        for index, item in enumerate(obj)
                    ]
                    return f"[<br>{'<br>'.join(items)}<br>{indent}{single_indent}]"
                return "[ ... ]"

            # build up a nice HTML formatted class name
            class_name = f"class <span style='font-weight: bold; font-style: italic'>{obj.__class__.__name__}</span>"

            # special case for QuerySet so we can inspect the query results
            if isinstance(obj, QuerySet):
                tree_length = obj.count()
                if tree_length == 0:
                    return _("{class_name} (empty query set) [ ]").format(class_name=class_name)
                if depth > 0:
                    # fetch the first five items
                    tree_items = obj.all()[:5 if tree_length <= 5 else 4]

                    items = [f"{indent}{single_indent}{index}: {_format_object(item, depth - 1, processed, level + 1)}"
                        for index, item in enumerate(tree_items)]
                    if tree_length > 5:
                        items.append(_("{indent}{single_indent}[ ... {more_items} additional items .. ]").format(more_items=tree_length - 4, indent=indent, single_indent=single_indent))

                    return _("{class_name} ({tree_length} item query set): [<br>{items}<br>{indent}]").format(class_name=class_name, tree_length=tree_length, items="<br>".join(items), indent=indent)
                return _("{class_name} ({tree_length} item query set) [ ... ]").format(class_name=class_name, tree_length=tree_length)

            # for custom objects, show the object type and its attributes.
            if depth > 0:
                attributes: Dict[str, Any] = {}
                class_attrs = inspect.classify_class_attrs(type(obj))
                attr_dict = {attr.name: attr for attr in class_attrs if attr.defining_class == type(obj)}

                for attr, details in attr_dict.items():
                    # todo: decide if this is wanted, and also if we should go back to dir(obj)
                    # if private/protected, or executable, skip
#                    if attr.startswith('_') or details.kind in ['method', 'class method', 'static method']:
#                        continue

                    attr_value: Any | None = getattr(obj, attr, None)
                    # some objects have "do_not_call_in_templates", so let's remove them since this
                    # is only for template display
                    if not getattr(attr_value, 'do_not_call_in_templates', False):
                        attributes[attr] = attr_value

                if len(attributes) == 0:
                    return f"{class_name}: {{ }}"

                items = [f"{indent}{single_indent}<span style='font-weight: bold'>{attr}:</span>: {_format_object(value, depth - 1, processed, level + 1)}"
                    for attr, value in attributes.items()]
                return f"{class_name}: {{<br>" + "<br>".join(items) + f"<br>{indent}}}"
            return f'{class_name}: {{ ... }}'
        return _('[ previously output ]')
    except Exception as e:   # pylint: disable=broad-except
        return _('Error in Explore: {err}').format(err = str(e))

@register.filter()
def explore(obj:Any, depth='2') -> str:
    """
    Filter to explore properties of an object for finding and understanding properties
    on various objects.  By default shows the first two levels of the object, but the
    parameter can specify a specific depth.  While attempts are made to avoid recursion
    (objects that point eventually back to themselves), not all objects work with this so
    very large depths can create massive output or even a stack overflow.

    Example:
    - part|show_properties:3    
    """
    # set up a dictionary to track objects in case of recursion
    processed: Dict[int, bool] = {}

    # decode the options
    try:
        int_depth = int(depth)
    except ValueError:
        int_depth = 2

    # format the object as HTML
    formatted_html = _format_object(obj, int_depth, processed)
    return mark_safe(formatted_html)


def _get_stock_items(part, location_name=None, min_on_hand=None):
    """
    Fetch all StockItems for a given part and optionally filter by StockLocation or its descendants,
    and by a minimum quantity on hand.

    Args:
        part (Part): The Part instance for which to find StockItems.
        location_name (str, optional): The name of the StockLocation to filter by. Defaults to None.
        min_on_hand (int, optional): The minimum quantity that must be on hand. Defaults to None.

    Returns:
        QuerySet: A queryset of StockItem instances.
    """
    # Start with all stock items for the given part
    stock_items = StockItem.objects.filter(part=part)

    # Filter by minimum quantity on hand if specified
    if min_on_hand is not None:
        stock_items = stock_items.filter(quantity__gte=min_on_hand)

    # If a location name is provided, further filter the stock items
    if location_name:
        try:
            # Get the StockLocation by name
            location = StockLocation.objects.get(name=location_name)
            # Get all descendants including the location itself
            locations = location.get_descendants(include_self=True)
            # Filter stock items by these locations
            stock_items = stock_items.filter(location__in=locations)
        except StockLocation.DoesNotExist:
            # If no such location exists, return an empty queryset
            return StockItem.objects.none()
    return stock_items

@register.simple_tag()
def stocklist(part: Part | int, min_quantity_on_hand: int, location: str) -> List[StockItem]:
    """
    Filter to get a list of stock items for a part, optionally filtering by a minimum number of
    available stock items and also limited to a location.  It returns a list of StockItem objects
    that match the criteria.  If a location is specified, it should be the extact name of a 
    location, and it will match that location and any children of that location.

    QUESTION: Shouldn't this really be about allocations?  Where did I make an allocation for
    the specific BOM?  This call is generic to a part, which has benefits, but in the use case
    of a BOM, we want to see what part(s) we allocated.

    Examples:
    - {% stocklist part as stock_list %}
    - {% stocklist list.part.pk 10 as stock_list as stock_list %}
    - {% stocklist part 0 "West Assembly Building" as stock_list %}
    """
    # get the part object if it is not already
    if isinstance(part, int):
        part = Part.objects.get(pk=part)

    if not part:
        return []

    # get the stock items for the part
    return _get_stock_items(part, location, min_quantity_on_hand)
