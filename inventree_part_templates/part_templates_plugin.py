""" 
    InvenTree-Part-Templates: A plugin for InvenTree that extends reporting (including label reports) with context variables
    that are built from category and part templates.  
"""

# Typing
from typing import Dict, Any, List

# Error reporting assistance
import traceback

# Plugin imports
from plugin import InvenTreePlugin
from plugin.mixins import ReportMixin, SettingsMixin, PanelMixin, UrlsMixin

# InvenTree models
from stock.models import StockItem
from part.models import Part, PartCategory

# Django templates
from django.template import Context, Template

# InvenTree views
from part.views import PartDetail, CategoryDetail
from stock.views import StockItemDetail

# Django views
from django.views.generic import UpdateView

# API support for URLs and JSON
from django.urls import path
from django.http import HttpResponse
import json

# Plugin version number
from .version import PLUGIN_VERSION


class PartTemplatesPlugin(PanelMixin, UrlsMixin, ReportMixin, SettingsMixin, InvenTreePlugin):
    """
    A plugin for InvenTree that extends reporting with customizable part / category templates.
    """

    # plugin metadata for identity in InvenTree
    NAME = "InvenTreePartTemplates"
    SLUG = "part-templates"
    TITLE = "InvenTree Part Templates"
    DESCRIPTION = "Extends reporting with customizable part / category templates"
    VERSION = PLUGIN_VERSION
    AUTHOR = "Chris Midgley"

    # plugin custom settings
    MAX_TEMPLATES = 5
    SETTINGS = {
        'T1_KEY': {
            'name': 'Template 1: Variable Name',
            'description': 'Context variable name',
            'default': 'description',
        },
        'T1_TEMPLATE': {
            'name': 'Template 1: Default template',
            'description': 'Template to use when no other templates are inherited',
            'default': '{{ part.name }}{% if part.IPN %} ({{ part.IPN }}){% endif %}',
        },
        'T2_KEY': {
            'name': 'Template 2: Variable Name',
            'description': 'Context variable name',
            'default': 'category',
        },
        'T2_TEMPLATE': {
            'name': 'Template 2: Default template',
            'description': 'Template to use when no other templates are inherited',
            'default': '{% if part.category.parent %} {{ part.category.parent.name }} / {% endif %}{{ part.category.name }}',
        },
        'T3_KEY': {
            'name': 'Template 3: Variable Name',
            'description': 'Context variable name',
            'default': '',
        },
        'T3_TEMPLATE': {
            'name': 'Template 3: Default template',
            'description': 'Template to use when no other templates are inherited',
            'default': '',
        },
        'T4_KEY': {
            'name': 'Template 4: Variable Name',
            'description': 'Context variable name',
            'default': '',
        },
        'T4_TEMPLATE': {
            'name': 'Template 4: Default template',
            'description': 'Template to use when no other templates are inherited',
            'default': '',
        },
        'T5_KEY': {
            'name': 'Template 5: Variable Name',
            'description': 'Context variable name',
            'default': '',
        },
        'T5_TEMPLATE': {
            'name': 'Template 5: Default template',
            'description': 'Template to use when no other templates are inherited',
            'default': '',
        },
    }

    # internal settings
    CONTEXT_KEY = 'part_templates'
    METADATA_PARENT = 'part_template_plugin'

    #
    # mixin entrypoints
    #

    def add_report_context(self, _report_instance, model_instance: Part | StockItem, _request, context: Dict[str, Any]) -> None:
        """
        Callback from InvenTree ReportMixin to add context to the report instance.

        Args:
            _report_instance: The report instance.
            model_instance: The model instance.
            _request: The request.
            context: The context dictionary.

        Returns:
            None
        """
        self._add_context(model_instance, context)

    def add_label_context(self, _label_instance, model_instance: Part | StockItem, _request, context: Dict[str, Any]) -> None:
        """
        Callback from InvenTree ReportMixin to add context to the label instance.

        Args:
            _report_instance: The report instance.
            model_instance: The model instance.
            _request: The request.
            context: The context dictionary.

        Returns:
            None
        """
        self._add_context(model_instance, context)

    def get_custom_panels(self, view: UpdateView, _request) -> List[Any]:
        panels = []

        if isinstance(view, PartDetail):
            panels.append({
                'title': 'Part Templates',
                'icon': 'fa-file-alt',
                'content_template': 'part_templates/part_detail_panel.html',
                # 'context': {
                #     'part': view.object,
                # }
            })
        elif isinstance(view, CategoryDetail):
            panels.append({
                'title': 'Category Templates',
                'icon': 'fa-file-alt',
                'content_template': 'part_templates/category_detail_panel.html',
                # 'context': {
                #     'category': view.object,
                # }
            })
        elif isinstance(view, StockItemDetail):
            panels.append({
                'title': 'Stock Templates',
                'icon': 'fa-file-alt',
                'content_template': 'part_templates/stock_detail_panel.html',
                # 'context': {
                #     'stock': view.object,
                # }
            })

        return panels

    def setup_urls(self):
        return [
                path("example/<int:layer>/<path:size>/",
                    self.do_something, name='transfer'),
        ]

    # Define the function that will be called.
    def do_something(self, _request, _layer, _size):
        # data = json.loads(request.body)
        return HttpResponse('OK')

    #
    # internal methods
    #

    def _add_context(self, instance: Part | StockItem, context: Dict[str, Any]) -> None:
        """
        Common handler for the InvenTree add context callbacks.  Locate the part from the instance,
        processes all context templates set up by the user, and attaches the results to the
        Django context.

        Args:
            instance (Part | StockItem): The instance for which the context variables are being added.
            context (Dict[str, Any]): The dictionary to which the context variables are being added.

        Returns:
            None
        """

        # make sure our instance has a part (Part and Stock)
        part = self._cast_part(instance)
        if part:
            # set up an empty context
            context[self.CONTEXT_KEY] = {}

            # process each possible key from settings
            for key_number in range(1, self.MAX_TEMPLATES + 1):
                key: str = self.get_setting(f'T{key_number}_KEY')
                default_template: str = self.get_setting(f'T{key_number}_TEMPLATE')
                # if the user has defined a key (context variable name), process this template
                if key:
                    # find the best template between part and the category metadata heirarchy
                    found_template = self._find_template(part, key, default_template)
                    stock: StockItem | None = instance if isinstance(instance, StockItem) else None
                    try:
                        result = self._apply_template(part, stock, found_template)
                    except Exception as e:      # pylint: disable=broad-except
                        tb = traceback.extract_tb(e.__traceback__)
                        last_call = tb[-1]
                        context[self.CONTEXT_KEY] = {
                                'error': f"Template error for {key} with \"{found_template}\": '{str(e)}' {last_call.filename}:{last_call.lineno}"
                        }
                        return

                    # success - add the key with the formatted result to context
                    context[self.CONTEXT_KEY][key] = result
        else:
            context[self.CONTEXT_KEY] = { 'error', f"Must use Part or StockItem (found {type(instance).__type__})" }

    def _cast_part(self, instance: Part | StockItem) -> Part | None:
        """
        Casts the given instance to a Part object if it is an instance of Part or a StockItem.

        Args:
            instance (Part | StockItem): The instance to cast or retrieve the Part object from.

        Returns:
            Part | None: The casted Part object if the instance is an instance of Part or StockItem,
            None otherwise.
        """
        if isinstance(instance, Part):
            return instance
        if isinstance(instance, StockItem):
            return instance.part
        return None


    def _apply_template(self, part: Part, stock: StockItem | None, template: str) -> str:
        """
        Apply a template to a part.  Sets up the data for the Django template, and asks
        for it to do the template formatting.

        Args:
            part (Part): The part object to apply the template to.
            stock (StockItem | None): If reporting on a stock item, the stock item this is for.
            template (str): The template string to apply.

        Returns:
            str: The formatted string after applying the template.
        """

        template_data = {
            'part': part,
            'stock': stock,
            'category': part.category,
            'parameters': part.get_parameters(),
        }

        # set up the Django template
        django_template = Template(template)
        # create the template context
        context = Context(template_data)
        # format the template
        return django_template.render(context)

    def _find_template(self, part: Part, key: str, default_template: str) -> str:
        """
        Find the template for a given part and key.  Starts by checking if the part has
        metadata and specifically this key.  If not, it walks up the category tree to find
        the first category with metadata and this key.  If none found, it uses the default
        template.

        Args:
            part (Part): The part for which to find the template.
            key (str): The key to search for in the part's metadata.
            default_template (str): The default template to use if the key is not found.

        Returns:
            str: The template found for the given part and key, or the default template if not found.
        """
        # does our part have our metadata?
        if part.metadata and part.metadata[self.METADATA_PARENT] and part.metadata[self.METADATA_PARENT].get(key):
            return part.metadata[self.METADATA_PARENT][key]

        # not on part, so walk up the category tree
        return self._find_category_template(part.category, key, default_template)

    def _find_category_template(self, category: PartCategory, key: str, default_template: str) -> str:
        """
        Recursively searches for a template associated with a given category and key.

        Args:
            category (PartCategory): The category to start the search from.
            key (str): The key to search for in the category's metadata.
            default_template (str): The default template to return if no template is found.

        Returns:
            str: The template associated with the category and key, or the default template if not found.
        """
        # if we have metadata with our key, use that as the template
        if category.metadata and category.metadata[self.METADATA_PARENT] and category.metadata[self.METADATA_PARENT].get(key):
            return category.metadata[self.METADATA_PARENT][key]

        # no template, so walk up the category tree
        if category.parent:
            return self._find_category_template(category.parent, key, default_template)
        return default_template
