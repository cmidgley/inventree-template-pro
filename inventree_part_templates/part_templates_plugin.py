""" 
    InvenTree-Part-Templates: A plugin for InvenTree that extends reporting (including label reports) with context variables
    that are built from category and part templates.  
"""

# Plugin imports
from plugin import InvenTreePlugin
from plugin.mixins import ReportMixin

# InvenTree models
from stock.models import StockItem
from part.models import Part

# Django templates
from django.template import Context, Template

# Error reporting assistance
import traceback

# Plugin version number
from inventree_part_templates.version import PLUGIN_VERSION

class PartTemplatesPlugin(ReportMixin, InvenTreePlugin):
    NAME = "InvenTreePartTemplates"
    SLUG = "part-templates"
    TITLE = "InvenTree Part Templates"
    DESCRIPTION = "Extends reporting with customizable part category templates"
    VERSION = PLUGIN_VERSION
    AUTHOR = "Chris Midgley"

    CONTEXT_KEY = 'part_templates'

    def add_report_context(self, report_instance, model_instance, request, context):
        self._addContext(model_instance, context)

    def add_label_context(self, label_instance, model_instance, request, context):
        self._addContext(model_instance, context)

    def _addContext(self, instance, context):
        # todo: use setting to determine templates and subkey names
        part = self._getPart(instance)
        if part:
            try:
                description = self._computeDescription(part)
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                lastCall = tb[-1]
                context[self.CONTEXT_KEY] = {
                        'error': f"Template error: '{str(e)}' {lastCall.filename}:{lastCall.lineno}"
                }
                return

            context[self.CONTEXT_KEY] = {
                'part': description,
                'category': part.category.name
            }
            if part.category.parent == 'Capacitors':
                context[self.CONTEXT_KEY]['category'] = part.category.name + ' ' + part.category.parent.name
        else:
            context[self.CONTEXT_KEY] = { 'error', f"Must use Part or StockItem (found {type(instance).__type__})" }

    def _getPart(self, instance):
        if isinstance(instance, Part):
            return instance
        elif isinstance(instance, StockItem):
            return instance.part
        else:
            return None


    def _computeDescription(self, part):
        templateData = {
            'part': part,
            'category': part.category
        }
        return self._format(templateData)

    def _findTemplate(self, category):
        # if we have metadata with our key, use that as the template
        if (category.metadata and category.metadata['autodescribe']):
            return category.metadata['autodescribe']
        # no template, so walk up the category tree
        if category.parent:
            return self._findTemplate(category.parent)
        return "{{ part.name }}{% if part.IPN %} ({{ part.IPN}}){% endif %}"

    def _format(self, templateData):
        # find the best template by walking  the category metadata heirarchy
        template = self._findTemplate(templateData['part'].category)
        # set up the Django template
        djangoTemplate = Template(template)
        # extend the data to include the category key
        templateData['category'] = templateData['part'].category
        # create the template context
        context = Context(templateData)
        # format the template
        return djangoTemplate.render(context)
