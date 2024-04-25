""" 
    InvenTree-Part-Templates: A plugin for InvenTree that extends reporting (including label reports) with context properties
    that are built from category and part context templates.  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from __future__ import annotations
from typing import Dict, Any, List, cast
from django.utils.translation import gettext_lazy as _
from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, ReportMixin, SettingsMixin, PanelMixin, UrlsMixin
from stock.models import StockItem
from part.models import Part, PartCategory
from part.views import PartDetail, CategoryDetail
from stock.views import StockItemDetail
from django.views.generic import UpdateView
from django.urls import path
from django.http import HttpResponse, HttpRequest, JsonResponse
from inventree_part_templates.constants import METADATA_PARENT, METADATA_TEMPLATE_KEY, MAX_TEMPLATES, TEMPLATETAGS_CONTEXT_PLUGIN
from .version import PLUGIN_VERSION
from django.contrib.auth.models import User
from .property_context import PropertyContext

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
            'description': _('Rules for when rendered context templates are shown in a Part Templates panel.'),
            'choices': [
                ('superuser',_('Only if user is Superuser')),
                ('always',_('Always allow Part Template viewing')),
                ('never',_('Never allow Part Template viewing'))],
            'default': 'superuser',
        },
        'T1_KEY': {
            'name': _('Template 1: Context property name'),
            'description': _('Name of the context property (used in templates such as "part_templates.my_name.")'),
            'default': 'description',
        },
        'T1_TEMPLATE': {
            'name': _('Template 1: Default template'),
            'description': _('Default template used when no other part of category template is found.'),
            'default': '{{ part.name|scrub:"MPN" }}{% if part.IPN %} ({{ part.IPN }}){% endif %}',
        },
        'T2_KEY': {
            'name': _('Template 2: Context property name'),
            'description': _('Name of the context property (used in templates such as "part_templates.my_name.")'),
            'default': 'category',
        },
        'T2_TEMPLATE': {
            'name': _('Template 2: Default template'),
            'description': _('Default template used when no other part of category template is found.'),
            'default': '{% if category.parent %} {{ category.parent.name }} / {% endif %}{{ category.name }}',
        },
        'T3_KEY': {
            'name': _('Template 3: Context property name'),
            'description': _('Name of the context property (used in templates such as "part_templates.my_name.")'),
            'default': '',
        },
        'T3_TEMPLATE': {
            'name': _('Template 3: Default template'),
            'description': _('Default template used when no other part of category template is found.'),
            'default': '',
        },
        'T4_KEY': {
            'name': _('Template 4: Context property name'),
            'description': _('Name of the context property (used in templates such as "part_templates.my_name.")'),
            'default': '',
        },
        'T4_TEMPLATE': {
            'name': _('Template 4: Default template'),
            'description': _('Default template used when no other part of category template is found.'),
            'default': '',
        },
        'T5_KEY': {
            'name': _('Template 5: Context property name'),
            'description': _('Name of the context property (used in templates such as "part_templates.my_name.")'),
            'default': '',
        },
        'T5_TEMPLATE': {
            'name': _('Template 5: Default template'),
            'description': _('Default template used when no other part of category template is found.'),
            'default': '',
        },
    }

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
        # add the rendered context properties based on model_instance to our context
        PropertyContext(model_instance).get_context(context, self)
        # add ourselves to the context so the templatetag can access our SettingsMixin
        context[TEMPLATETAGS_CONTEXT_PLUGIN] = self

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
        # add the rendered context properties based on model_instance to our context
        PropertyContext(model_instance).get_context(context, self)
        # add ourselves to the context so the templatetag can access our SettingsMixin
        context[TEMPLATETAGS_CONTEXT_PLUGIN] = self

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
            view (UpdateView): The view object (PartDetail or CategoryDetail)
            request (HtpRequest): The request object.  
            context (Dict[str, Any]): The context dictionary.

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
        for key_number in range(1, MAX_TEMPLATES + 1):
            key: str = self.get_setting(f'T{key_number}_KEY')
            default_template: str = self.get_setting(f'T{key_number}_TEMPLATE')

            # determine the parent category so we can pick up what would be the inherited template
            # if this does not override it
            parent_category = instance.category if isinstance(instance, Part) else instance.parent

            # get the template metadata, which is a dictionary of context_name: template for this instance
            #instance = Part.objects.get(pk=instance.pk)
            if instance.metadata and instance.metadata.get(METADATA_PARENT) and instance.metadata[METADATA_PARENT].get(METADATA_TEMPLATE_KEY):
                metadata_templates = instance.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY]
            else:
                metadata_templates = {}

            # get the instance-specific template for this key
            template = metadata_templates.get(key, '')

            # get the inherited template (ignoring our current template, this is what it would be if
            # the template on this instance was not defined)
            inherited_template = PropertyContext.find_category_template(parent_category, key, default_template)

            # render the part using the context if we have one
            rendered_template = ""
            if isinstance(instance, Part):
                try:
                    rendered_template = PropertyContext(instance).apply_template(template if template else inherited_template)
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
        for key_number in range(1, MAX_TEMPLATES + 1):
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
        if not instance.metadata.get(METADATA_PARENT):
            instance.metadata[METADATA_PARENT] = {}
        if not instance.metadata[METADATA_PARENT].get(METADATA_TEMPLATE_KEY):
            instance.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY] = {}

        # set or delete the key using template
        try:
            if template:
                instance.metadata[METADATA_PARENT].get(METADATA_TEMPLATE_KEY)[key] = template
                instance.save()
            elif instance.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY].get(key):
                del instance.metadata[METADATA_PARENT][METADATA_TEMPLATE_KEY][key]
                instance.save()
        except Exception as e:      # pylint: disable=broad-except
            return JsonResponse({
                'status': 'error',
                'message': _("Error saving template: {(error}").format(error=str(e))
            }, status=200)

        return JsonResponse({'status': 'ok', 'message': _('Template saved successfully') })
