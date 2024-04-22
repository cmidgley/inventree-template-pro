""" 
    Custom Django template tags for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

# for regex
import re

# for debugging
import pprint

# for reading YAML config file
import os
import yaml
from pathlib import Path

# to add Django filters / tags
from django import template
from django.template import Context

# for locating parts using the primary key
from part.models import Part

# translation support
from django.utils.translation import gettext_lazy as _

# caching of the YAML data
from django.core.cache import cache

# type hinting
from typing import Dict, List

# class to manage the property context
from inventree_part_templates.property_context import PropertyContext

# constants
from inventree_part_templates.constants import TEMPLATETAGS_CONTEXT_PLUGIN

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

    return template_context.get('part_templates')

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
    """Access to value of a dictionary by key (no scrubbing)

    Example:
    {% parameters|value:"Rated Voltage" %}
    """
    try:
        return properties.get(key)
    except Exception:       # pylint: disable=broad-except
        return ""

@register.filter()
def item(properties: Dict[str, str], key: str) -> str | None:
    """Access to value of a dictionary by key (with scrubbing)

    Example:
    {% parameters|item:"Package Type" %}
    """
    try:
        item_value = properties.get(key)
    except Exception:       # pylint: disable=broad-except
        return ""

    if item_value:
        return scrub(item_value, key)
    return ""
