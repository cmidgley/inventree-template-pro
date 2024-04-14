""" 
    Custom Django template tags for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

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
        cache.set('yaml_data', filters, timeout=CACHE_TIMEOUT)
    return filters

@register.simple_tag()
def prop_filter(name: str) -> str:
    try:
        config = load_filters()
    except FileNotFoundError as error:
        return(_('["part_templates.yaml" not found: {error}]').format(error=str(error)))
    except yaml.YAMLError as error:
        return(_("[Error in configuration file: {error}]").format(error=str(error)))

    filters = config.get('filters')
    if filters is None:
        return _('["filters" not found in "parts_templates.yaml"]')
    rules = filters.get(name)
    if rules is None:
        return _('["{name}" not found in "parts_templates.yaml"]').format(name=name)

    return f"First rule: {rules[0].get('pattern')}"

@register.filter
def prop(properties: dict[str, str], key: str) -> str | None:
    """Access to key of supplied dict (properties).

    Usage:
    {% properties|prop:name %}
    """
    return properties.get(key)


@register.filter
def segment(value: str, words: str = "1") -> str:
    try:
        word_count = int(words)
    except ValueError:
        word_count = 1

    result = value.split()[:word_count]
    return ' '.join(result)
