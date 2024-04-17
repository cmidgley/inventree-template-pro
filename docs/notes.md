
## Installation

`part-templates-plugin` is [installed like most
plugins](https://docs.inventree.org/en/latest/extend/plugins/install/).
It can be installed with using plugins in settings, via PIP, or using the plugins.txt file
(recommended if using Docker).  

This plugin requires the `Enable URL integration` plugin setting to be enabled as it needs to
perform REST API calls to InvenTree to edit and delete templates.

Don't forget to enable the plugin after adding it.


## Plugin Configuration

Under `Settings / Plugin Settings / InvenTree Part Templates` you will find the settings for the
plug-in.  

TODO: CONTINUE FROM HERE

## Template Configuration

## Label and Report Usage



## Example Usage

Consider a scenario where you want to create a part description template named "part_description"
using parameters from the part such as `part.Resistance` and `part.Capacitance`.

After defining a part template called `part_description`, you can refer to the following in your labeling or reporting templates:

```django
{{ part_templates.part_description }}
```

### Default Template

You can define a default template to apply across all parts unless specifically overridden:

```django
{{ part.name }}{% if part.IPN %} ({{ part.IPN }}){% endif %}
```

This default setting ensures that each part, at a minimum, is described by its name and optionally
includes the Internal Part Number (IPN) if available.

### Category-Specific Overrides

For specific categories like "Passive / Resistor", you could customize the template to highlight essential attributes:

```django
{{ part.Resistance }} {{ part.wattage }} {{ part.package }}
```

This customization would automatically apply to all sub-categories of "Resistor" unless they have their own defined templates, promoting a structured yet flexible template inheritance system.

### Part-Specific Overrides

Individual parts can also have template overrides, allowing for exceptions to the category-based templates where necessary.

## Defining part / category templates

An template is a standard Django template, just as used by InvenTree for labels and reports.  The
[context variables](https://docs.inventree.org/en/stable/report/context_variables/) provided are:

* `part`: This is the part that the report or label is working on.  If the report/label is on a
  `Stock`, this will represent the part of the stock being reported.
* `category`: This is the leaf category of the part.  It's a shorthand for `part.category`.
* `stock`: If the report is using stock, then this is the stock object.  You can test for this with
  `{% if part_templates.stock %}this is stock{% end if %}`.
* `parameters`: The parameters associated with the part.  This is a shorthand for `part.parameters`.

Some examples:

* `{{ part.name }}` will output the part name
* `{{ parameters.Resistance }}` will output the part's 'Resistence' parameter
* `{{ parameters['Rated Voltage']}}` is the syntax for parameters with spaces in their names
* `{{ category.name }} Cap: {{ parameters.Capacitance }} {{ parameters['Rated Voltage'] }} {{
  parameters['Tolerance'] }} {{ parameters['Mounting Type']}}`: Assuming the properties are defined,
  something like `Ceramic Cap: 0.1uF 50 V 10% SMT`


## Assigning templates to categories and parts

***** TO BE DONE *****

## Use in Reports and Labels

Using `inventree-part-template` in a label or report, once you have defined the part/category templates, is simple: a new
context variable is available called `part_templates` that has a property for each template created, using the name specified
in the plugin setup.  

For example, let's say you created `category` as the first template name, and `description` as the second.  In your report / label, you just refer to them like other context variables:

```django
{{ part_templates.category }}<br>
{{ part_templates.description }}
```

There is one special property called `error`.  This is normally `None` but is set when there was an
error processing the templates.  A best practice for a report/label might be:

```django
{% if not part_templates %}
    <div class="error">Plugin inventree-part-templates required</div>
{% elif part_templates.error %}
    <div class="error">{{ error }}<div>
{% else %}
(your label/report as normal)
{% endif %}
```

## TODO

* document the 'error' property
* document a recommend label/report structure to test for existance
* document the yaml file (and [RegEx tester recommenation](https://regex101.com/))