""" 
    Custom Django template tags for the inventree-template-pro plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

import os
import re
from pathlib import Path
from typing import Dict, List
import yaml

from .shared import register
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache

# set how long we cache the config data (in seconds), to allow users to edit it without restarting the server
CACHE_TIMEOUT = 3

# define the types for the yaml config file
FilterRule = Dict[str, str]
FilterRules = List[FilterRule]
Filters = Dict[str, FilterRules]
Config = Dict[str, Filters]

def load_filters() -> Config:
    """
    Provides the filters from the configuration file, from cache or by loading the file.  The file
    path and name can be defined in the environment variable TEMPLATE_PRO_CONFIG_FILE, or it will
    default to 'template_pro.yaml' in the inventree-template-pro plugin directory.

    Returns:
        Config: The loaded filters from the configuration file.
    """
    # do we have config cached?
    filters: Config | None = cache.get('template-pro-yaml')
    if not filters:
        # set the path to the config file using environment variable PART_TEPLATES_CONFIG_FILE, or
        # get from the plugin directory if not set
        cfg_filename = os.getenv('TEMPLATE_PRO_CONFIG_FILE')
        if cfg_filename:
            cfg_filename = Path(cfg_filename.strip()).resolve()
        else:
            cfg_filename = Path(__file__).parent.parent.joinpath('template_pro.yaml').resolve()

        # load the config file
        with open(cfg_filename, 'r', encoding='utf-8') as file:
            loaded_data = yaml.safe_load(file)
            if (loaded_data is None) or (not isinstance(loaded_data, dict)):
                raise FileNotFoundError(_("File found but contents missing or not dictionary: {cfg_filename}").format(cfg_filename=cfg_filename))
            filters = loaded_data

        # cache the config data
        cache.set('template-pro-yaml', filters, timeout=CACHE_TIMEOUT)
    return filters

@register.filter()
def scrub(scrub_string: str, name: str) -> str:
    """
    Scrubs a string (typically from a part parameter) using rules defined in the template_pro.yaml
    file based on the supplied name.  The rules are defined in the configuration file as a list of
    dictionaries, where each dictionary contains a pattern and replacement key using regex.

    Example:
    - {% part.name|scrub:"MPN" %}
    """
    if not name:
        return _('[scrub missing required :name]')

    try:
        config = load_filters()
    except FileNotFoundError as error:
        return (_('["template_pro.yaml" not found or invalid: {error}]').format(error=str(error)))
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
