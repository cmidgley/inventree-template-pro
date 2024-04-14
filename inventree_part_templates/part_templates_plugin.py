""" 
    InvenTree-Part-Templates: A plugin for InvenTree that extends reporting (including label reports) with context variables
    that are built from category and part templates.  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

# Typing
from typing import Dict, Any, List

# Error reporting assistance
import traceback

# Translation support
from django.utils.translation import gettext_lazy as _

# Plugin imports
from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, ReportMixin, SettingsMixin, PanelMixin, UrlsMixin

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

# API support for URLs
from django.urls import path
from django.http import HttpResponse, HttpRequest, JsonResponse

# Plugin version number
from .version import PLUGIN_VERSION

# User support
from django.contrib.auth.models import User
from typing import cast

class PartTemplatesPlugin(AppMixin, PanelMixin, UrlsMixin, ReportMixin, SettingsMixin, InvenTreePlugin):
    """
    A plugin for InvenTree that extends reporting with customizable part / category templates.
    """

    # plugin metadata for identity in InvenTree
    NAME = "PartTemplatesPlugin"
    SLUG = "part-templates"
    TITLE = _("InvenTree Part Templates")
    DESCRIPTION = _("Extends reporting with customizable part / category templates")
    VERSION = PLUGIN_VERSION
    AUTHOR = "Chris Midgley"

    # plugin custom settings
    MAX_TEMPLATES = 5
    SETTINGS = {
        'EDITING': {
            'name': _('Panel editing'),
            'description': _('Rules for when Part Templates may be edited in a Part Templates panel.'),
            'choices': [
                ('superuser',_('Only if user is Superuser')),
                ('always',_('Always allow Part Template editing')),
                ('never',_('Never allow Part Template editing'))],
            'default': 'superuser',
        },
        'VIEWING': {
            'name': _('Panel viewing'),
            'description': _('Rules for when rendered context variables are shown in a Part Templates panel.'),
            'choices': [
                ('superuser',_('Only if user is Superuser')),
                ('always',_('Always allow Part Template viewing')),
                ('never',_('Never allow Part Template viewing'))],
            'default': 'superuser',
        },
        'T1_KEY': {
            'name': _('Template 1: Variable Name'),
            'description': _('Context variable name'),
            'default': 'description',
        },
        'T1_TEMPLATE': {
            'name': _('Template 1: Default template'),
            'description': _('Template to use when no other templates are inherited'),
            'default': '{{ part.name|scrub:"MPN" }}{% if part.IPN %} ({{ part.IPN }}){% endif %}',
        },
        'T2_KEY': {
            'name': _('Template 2: Variable Name'),
            'description': _('Context variable name'),
            'default': 'category',
        },
        'T2_TEMPLATE': {
            'name': _('Template 2: Default template'),
            'description': _('Template to use when no other templates are inherited'),
            'default': '{% if category.parent %} {{ category.parent.name }} / {% endif %}{{ category.name }}',
        },
        'T3_KEY': {
            'name': _('Template 3: Variable Name'),
            'description': _('Context variable name'),
            'default': '',
        },
        'T3_TEMPLATE': {
            'name': _('Template 3: Default template'),
            'description': _('Template to use when no other templates are inherited'),
            'default': '',
        },
        'T4_KEY': {
            'name': _('Template 4: Variable Name'),
            'description': _('Context variable name'),
            'default': '',
        },
        'T4_TEMPLATE': {
            'name': _('Template 4: Default template'),
            'description': _('Template to use when no other templates are inherited'),
            'default': '',
        },
        'T5_KEY': {
            'name': _('Template 5: Variable Name'),
            'description': _('Context variable name'),
            'default': '',
        },
        'T5_TEMPLATE': {
            'name': _('Template 5: Default template'),
            'description': _('Template to use when no other templates are inherited'),
            'default': '',
        },
    }

    # internal settings
    CONTEXT_KEY = 'part_templates'
    METADATA_PARENT = 'part_template_plugin'
    METADATA_TEMPLATE_KEY = 'templates'

    #
    # Report mixin entrypoints
    #

    def add_report_context(self, _report_instance, model_instance: Part | StockItem, _request: HttpRequest, context: Dict[str, Any]) -> None:
        """
        Callback from InvenTree ReportMixin to add context to the report instance.

        Args:
            _report_instance: The report instance.
            model_instance (Part | StockItem): The model instance.
            _request (HttpRequest): The request.
            context (Dict[str, Any]): The context dictionary.

        Returns:
            None
        """
        self._add_context(model_instance, context)

    def add_label_context(self, _label_instance, model_instance: Part | StockItem, _request: HttpRequest, context: Dict[str, Any]) -> None:
        """
        Callback from InvenTree ReportMixin to add context to the label instance.

        Args:
            _label_instance: The label instance.
            model_instance (Part | StockItem): The model instance.
            _request (HttpRequest): The request.
            context (Dict[str, Any]): The context dictionary.

        Returns:
            None
        """
        self._add_context(model_instance, context)

    #
    # Panel mixin entrypoints
    #

    def get_panel_context(self, view: UpdateView, request: HttpRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieves the panel context for the given view, when PartDetail or CategoryDetail and
        settings EDITING and VIEWING indiate the panel should be shown.  The context name is
        'part_templates' and is a list of entries one per template context variable defined in the
        plugin settings.  Each entry contains the key name (key), the template associated with the
        key (template), and the inherited template for the key (inherited_template).  The inherited
        template is the template that would be used if the template on the instance was not defined.

        Args:
            view (UpdateView): The view object.  request (HtpRequest): The request object.  context
            (Dict[str, Any]): The context dictionary.

        Returns:
            Dict[str, Any]: The updated context dictionary.
        """

        # pick up our context from the super
        ctx = super().get_panel_context(view, request, context)

        # are we providing a panel?
        if not self._may_edit_panel(request, view) and not self._may_view_panel(request, view):
            return ctx

        # add our context
        ctx['part_templates'] = self._get_panel_context(view.get_object())
        ctx['part_templates_may_edit'] = self._may_edit_panel(request, view)
        ctx['part_templates_may_view'] = self._may_view_panel(request, view)

        return ctx

    def get_custom_panels(self, view: UpdateView, request: HttpRequest) -> List[Any]:
        """
        Retrieves our custom panel, if it is enabled and on a supported view.

        Args:
            view (UpdateView): The view object.
            request (HttpRequest): The request object.

        Returns:
            List[Any]: A list of custom panels.

        """
        panels = []

        # are we providing a panel?
        if not self._may_edit_panel(request, view) and not self._may_view_panel(request, view):
            return panels

        # add our panel
        panels.append({
            'title': 'Part Templates',
            'icon': 'fa-file-alt',
            'content_template': 'part_templates/part_detail_panel.html',
            'javascript': 'onPartTemplatesPanelLoad();'
        })

        return panels

    #
    # private method support for panel
    #

    def _get_panel_context(self, instance: Part | PartCategory) -> List[Dict[str, str]]:
        """
        Get the panel context containing a list of the plugin's configured context variables, and
        for each include the key name (key), the template associated with the key (template), and
        the inherited template for the key (inherited_template).  The inherited template is the
        template that would be used if the template on the instance was not defined.

        Args:
            instance (Part | PartCategory): The instance for which to retrieve the panel context.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the panel context.
                Each dictionary contains the following keys:
                - 'key': The context variable name.
                - 'template': The template associated with the context variable.
                - 'inherited_template': The inherited template for the context variable.
                - 'rendered_template': The template value rendered, if the part is available.
                - 'entity': the name of the entity being edited (Part, StockItem)
                - 'pk': The primary key of the entity object
        """
        context: List[Dict[str, str]] = []

        # process each possible key from settings
        for key_number in range(1, self.MAX_TEMPLATES + 1):
            key: str = self.get_setting(f'T{key_number}_KEY')
            default_template: str = self.get_setting(f'T{key_number}_TEMPLATE')

            # determine the parent category so we can pick up what would be the inherited template
            # if this does not override it
            parent_category = instance.category if isinstance(instance, Part) else instance.parent

            # get the template metadata, which is a dictionary of context_name: template for this instance
            #instance = Part.objects.get(pk=instance.pk)
            if instance.metadata and instance.metadata.get(self.METADATA_PARENT) and instance.metadata[self.METADATA_PARENT].get(self.METADATA_TEMPLATE_KEY):
                metadata_templates = instance.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY]
            else:
                metadata_templates = {}

            # get the instance-specific template for this key
            template = metadata_templates.get(key, '')

            # get the inherited template (ignoring our current template, this is what it would be if
            # the template on this instance was not defined)
            inherited_template = self._find_category_template(parent_category, key, default_template)

            # render the part using the context if we have one
            rendered_template = ""
            if isinstance(instance, Part):
                try:
                    rendered_template = self._apply_template(instance, None, template if template else inherited_template)
                except Exception as e:      # pylint: disable=broad-except
                    rendered_template = f'({_("error")}: {str(e)})'

            # if the user has defined a key (context variable name), add to our context
            if key:
                context.append({
                    'key': key,
                    'template': template,
                    'inherited_template': inherited_template,
                    'rendered_template': rendered_template,
                    'entity': 'part' if isinstance(instance, Part) else 'category',
                    'pk': instance.pk,
                })

        return context

    def _may_edit_panel(self, request: HttpRequest, view: UpdateView) -> bool:
        """
        Determines whether the panel can be edited based on the current settings and user permissions.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            bool: True if the panel can be edited, False otherwise.
        """
        # check if settings allow editing
        if self.get_setting('EDITING') == 'never':
            return False
        if self.get_setting('EDITING') == 'superuser' and not cast(User, request.user).is_superuser:
            return False

        # make sure it's a view we support editing on
        if not isinstance(view, (PartDetail, CategoryDetail)):
            return False

        return True

    def _may_view_panel(self, request: HttpRequest, view: UpdateView) -> bool:
        """
        Determines whether the panel can be viewed based on the user's permissions and settings.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            bool: True if the panel can be viewed, False otherwise.
        """
        # check if settings allow viewing
        if self.get_setting('VIEWING') == 'never':
            return False
        if self.get_setting('VIEWING') == 'superuser' and not cast(User, request.user).is_superuser:
            return False

        # make sure it's a view we support viewing on
        if not isinstance(view, (PartDetail, StockItemDetail)):
            return False

        return True

    #
    # Urls mixin entrypoints
    #

    def setup_urls(self):
        """
        Sets up the URLs for the part templates plugin, which simply saves the template string
        (query string template) to the key/entity (part/category) and pk (id of the part/category).

        Returns:
            A list of URL patterns for the part templates plugin.
        """
        return [
            path('set_template/<str:key>/<str:entity>/<int:pk>/', self._webapi_set_template, name='set_template'),
        ]

    def _webapi_set_template(self, request: HttpRequest, key: str, entity: str, pk: int) -> HttpResponse:
        """
        Web API endpoint for the panel frontend to delete a template from the database.

        Args:
            request (HttpRequest): The HTTP request object.
            key (str): The API key.
            entity (str): The entity name.
            pk (int): The primary key of the template to delete.

        Returns:
            HttpResponse: The HTTP response indicating the result of the deletion.
        """
        template = request.GET.get('template')
        if template is None:
            # If the required parameter is not present, return an error
            return JsonResponse({
                'status': 'error',
                'message': _('Missing required parameter: template')
            }, status=200)

        # locate this pk on the specified entity
        if entity == 'part':
            instance = Part.objects.get(pk=pk)
        elif entity == 'category':
            instance = PartCategory.objects.get(pk=pk)
        else:
            return JsonResponse({
                'status': 'error',
                'message': _('Invalid entity type: {entity}').format(entity=entity)
            }, status=200)

        # did we locate the entity?
        if not instance:
            return JsonResponse({
                'status': 'error',
                'message': _("Could not locate {entity} {pk}").format(entity=entity, pk=pk)
            }, status=200)

        # is key valid?
        for key_number in range(1, self.MAX_TEMPLATES + 1):
            setup_key: str = self.get_setting(f'T{key_number}_KEY')
            if key == setup_key:
                break
        else:
            return JsonResponse({
                'status': 'error',
                'message': _("Invalid key {key}").format(key=key)
            }, status=200)

        # set up our metadata
        if not instance.metadata:
            instance.metadata = {}
        if not instance.metadata.get(self.METADATA_PARENT):
            instance.metadata[self.METADATA_PARENT] = {}
        if not instance.metadata[self.METADATA_PARENT].get(self.METADATA_TEMPLATE_KEY):
            instance.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY] = {}

        # set or delete the key using template
        try:
            if template:
                instance.metadata[self.METADATA_PARENT].get(self.METADATA_TEMPLATE_KEY)[key] = template
                instance.save()
            elif instance.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY].get(key):
                del instance.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY][key]
                instance.save()
        except Exception as e:      # pylint: disable=broad-except
            return JsonResponse({
                'status': 'error',
                'message': _("Error saving template: {(error}").format(error=str(e))
            }, status=200)

        return JsonResponse({'status': 'ok', 'message': _('Template saved successfully') })

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
                                'error': _("Template error for {key} with \"{found_template}\": '{error}' {last_call.filename}:{last_call.lineno}").format(key=key, found_template=found_template, error=str(e), last_call=last_call)
                        }
                        return

                    # success - add the key with the formatted result to context
                    context[self.CONTEXT_KEY][key] = result
        else:
            context[self.CONTEXT_KEY] = { 'error', _("Must use Part or StockItem (found {type})").format(type=type(instance).__type__) }

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
            'parameters': part.parameters_map(),
        }

        # set up the Django template
        django_template = Template("{% load barcode report part_templates %}" + template)
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
        if part.metadata and part.metadata.get(self.METADATA_PARENT) and part.metadata[self.METADATA_PARENT].get(self.METADATA_TEMPLATE_KEY) and part.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY].get(key):
            return part.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY][key]

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
        # if no category, return default
        if not category:
            return default_template

        # if we have metadata with our key, use that as the template
        if category.metadata and category.metadata.get(self.METADATA_PARENT) and category.metadata[self.METADATA_PARENT].get(self.METADATA_TEMPLATE_KEY) and category.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY].get(key):
            return category.metadata[self.METADATA_PARENT][self.METADATA_TEMPLATE_KEY][key]

        # no template, so walk up the category tree
        return self._find_category_template(category.parent, key, default_template)
