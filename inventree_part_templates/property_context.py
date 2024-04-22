""" 
    Manages the templates and context to resolve part templates to strings for inventree-part-templates.

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

# Error reporting assistance
import traceback

# Typing
from typing import Dict, Any, List

# Translation support
from django.utils.translation import gettext_lazy as _

# Django templates
from django.template import Context, Template

# InvenTree models
from stock.models import StockItem
from part.models import Part, PartCategory

# Settings mixing to access plugin specific settings
from plugin.mixins import SettingsMixin

# constants
from inventree_part_templates.constants import METADATA_PARENT, METADATA_TEMPLATE_KEY, CONTEXT_KEY, MAX_TEMPLATES


#
# Main class that manages templates and property context
#
class PropertyContext:
    """
    The PropertyContext class is responsible for processing context templates set up by the user for a part.
    It handles the Django templating system and provides the context variables to the Django context
    for access the template renderings.

    Args:
        entity (Part | StockItem | int): The entity for which the context is being generated.  If an
        int, it is assumed to be a primary key for a Part object and will load the object from the
        Part model.
    """
    def __init__(self, entity: Part | StockItem | int):
        self._entity = entity
        self._part = self._cast_entity_to_part(entity)

    def get_context(self, context: Dict[str, Any], plugin: SettingsMixin) -> None:
        """
        Processes all context templates set up by the user for a part, and attaches the results to
        the Django context.

        Args:
            context (Dict[str, Any]): The dictionary to which the context variables are being added.

        Returns:
            None
        """
        if self._part:
            # set up an empty context
            context[CONTEXT_KEY] = {}

            # process each possible key from settings
            for key_number in range(1, MAX_TEMPLATES + 1):
                key: str = plugin.get_setting(f'T{key_number}_KEY')
                default_template: str = plugin.get_setting(f'T{key_number}_TEMPLATE')
                # if the user has defined a key (context variable name), process this template
                if key:
                    # find the best template between part and the category metadata heirarchy
                    found_template = self._find_template(key, default_template)
                    try:
                        result = self.apply_template(found_template)
                    except Exception as e:      # pylint: disable=broad-except
                        tb = traceback.extract_tb(e.__traceback__)
                        last_call = tb[-1]
                        context[CONTEXT_KEY] = {
                                'error': _("Template error for {key} with \"{found_template}\": '{error}' {last_call.filename}:{last_call.lineno}").format(key=key, found_template=found_template, error=str(e), last_call=last_call)
                        }
                        return

                    # success - add the key with the formatted result to context
                    context[CONTEXT_KEY][key] = result
        else:
            context[CONTEXT_KEY] = { 'error', _("Must use Part or StockItem (found {type})").format(type=self._entity if isinstance(self._entity, int) else type(self._entity).__type__) }

    def get_part(self) -> Part | None:
        """
        Returns the part associated with this context, or None if no part found.

        Returns:
            Part | None: The part located (as provided to the constructor and located) or None if no part found.
        """
        return self._part

    def apply_template(self, template: str) -> str:
        """
        Apply a template to a part.  Sets up the data for the Django template, and asks
        for it to do the template formatting.

        Args:
            template (str): The template string to apply.

        Returns:
            str: The formatted string after applying the template.
        """

        if not self._part:
            return ""

        template_data = {
            'part': self._part,
            'stock': self._entity if isinstance(self._entity, StockItem) else None,
            'category': self._part.category,
            'parameters': self._part.parameters_map(),
        }

        # set up the Django template
        django_template = Template("{% load barcode report part_templates %}" + template)
        # create the template context
        context = Context(template_data)
        # format the template
        return django_template.render(context)

    def _cast_entity_to_part(self, entity: Part | StockItem) -> Part | None:
        """
        Casts the given instance to a Part object if it is an instance of Part or a StockItem, or a
        primary key for a part.

        Args:
            entity (Part | StockItem | int): The instance to cast or retrieve the Part object from.

        Returns:
            Part | None: The casted Part object if the instance is an instance of Part or StockItem,
            None otherwise.
        """
        if isinstance(entity, Part):
            return entity
        if isinstance(entity, StockItem):
            return entity.part
        if isinstance(entity, int):
            try:
                return Part.objects.get(pk=entity)
            except Part.DoesNotExist:
                return None
        return None

    def _find_template(self, key: str, default_template: str) -> str:
        """
        Find the template for a given part and key.  Starts by checking if the part has
        metadata and specifically this key.  If not, it walks up the category tree to find
        the first category with metadata and this key.  If none found, it uses the default
        template.

        Args:
            key (str): The key to search for in the part's metadata.
            default_template (str): The default template to use if the key is not found.

        Returns:
            str: The template found for the given part and key, or the default template if not found.
        """
        if not self._part:
            return default_template

        # does our part have our metadata?
        if self._part.metadata and self._part.metadata.get(METADATA_PARENT) and self._part.metadata[METADATA_PARENT].get(METADATA_TEMPLATE_KEY) and self._part.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY].get(key):
            return self._part.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY][key]

        # not on part, so walk up the category tree
        return PropertyContext.find_category_template(self._part.category, key, default_template)

    @staticmethod
    def find_category_template(category: PartCategory, key: str, default_template: str) -> str:
        """
        Recursively searches for a template associated with a given category and key.

        Args:
            category (PartCategory): The category to start the search from.
            key (str): The key to search for in the category's metadata.
            default_template (str): The default template to return if no template is found.

        Returns:
            str: The template associated with the category and key, or the default template if not found.
        """
        # if no category, return default
        if not category:
            return default_template

        # if we have metadata with our key, use that as the template
        if (category.metadata
            and category.metadata.get(METADATA_PARENT)
            and category.metadata[METADATA_PARENT].get(METADATA_TEMPLATE_KEY)
            and category.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY].get(key)):
            return category.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY][key]

        # no template, so walk up the category tree
        return PropertyContext.find_category_template(category.parent, key, default_template)
