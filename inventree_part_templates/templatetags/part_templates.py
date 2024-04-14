""" 
    Custom Django template tags for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

# for regex
import re

# For reading YAML config file
import os
import yaml
from pathlib import Path

# To add Django filters / tags
from django import template

# Translation support
from django.utils.translation import gettext_lazy as _

# caching of the YAML data
from django.core.cache import cache

# for context in filters
from django.template import Context

# type hinting
from typing import Dict, List, Union

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
    filters = cache.get('part-templates-yaml')
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
            filters = yaml.safe_load(file)

        # cache the config data
        cache.set('part-templates-yaml', filters, timeout=CACHE_TIMEOUT)
    return filters

@register.filter()
def scrub(value: str, name: str) -> str:
    """
    Scrubs a value (typically from a part parameter) using rules defined in the part_templates.yaml
    file based on the supplied name.  The rules are defined in the configuration file as a list of
    dictionaries, where each dictionary contains a pattern and replacement key using regex.

    Args:
        value (str): The value to be scrubbed.
        name (str): The name of the rule to be applied.

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
        return (_('["part_templates.yaml" not found: {error}]').format(error=str(error)))
    except yaml.YAMLError as error:
        return (_("[Error in configuration file: {error}]").format(error=str(error)))

    filters = config.get('filters')
    if filters is None:
        return _('["filters" not found in "parts_templates.yaml"]')
    rules = filters.get(name)
    if rules is None:
        # return _('["{name}" not found in "parts_templates.yaml"]').format(name=name)
        return value

    for rule in rules:
        pattern = rule.get('pattern')
        if pattern is None:
            return _('["pattern" not found in "{name}" in "parts_templates.yaml"]').format(name=name)
        replacement = rule.get('replacement')
        if replacement is None:
            return _('["replacement" not found in "{name}" in "parts_templates.yaml"]').format(name=name)

        try:
            value = re.sub(pattern, replacement, value)
        except re.error as error:
            return _('["{name}" regex error on {pattern}: {error}]').format(name=name, pattern=pattern, error=str(error))

    return value

@register.filter()
def item(properties: Dict[str, str], key: str) -> str | None:
    """Access to key of supplied dict (typically parameters).

    Example:
    {% parameters|item:"Rated Voltage" %}
    """
    try:
        return properties.get(key)
    except Exception:       # pylint: disable=broad-except
        return ""

@register.filter()
def item_scrub(properties: Dict[str, str], key: str) -> str | None:
    """Access to key of supplied dict (parameters), that is then scrubbed (see scrub)

    Example:
    {% parameters|item_scrub:"Rated Voltage" %}
    """
    try:
        value = properties.get(key)
    except Exception:       # pylint: disable=broad-except
        return ""

    if value:
        return scrub(value, key)
    return ""
