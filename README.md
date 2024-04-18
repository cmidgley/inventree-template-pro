Have you spent a ton of time and energy managing your parts in [InvenTree](https://inventree.org)
to have detailed parameters, only to get labels (or lines in your reports) that look like this?

<img alt="C25076 | 0402WGF1000TCE" src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/default-label-example.png" style="border: black 1px solid" width="200px">

Wouldn't you rather have concise, detailed information about the part, specific to each part type,
using InvenTree parameters?

<img alt="100ohm 62.5mw 1% SMD 0402" src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/29mm-label-example.png" style="border: black 1px
solid" width="200px">

# InvenTree Part Templates

**InvenTree-Part-Templates** is a plugin for InvenTree that extends InvenTree label and reporting
templates.  You create new custom context properties, adjust template values for those properties as
desired based on the category of the parts, and use the `part_templates` context variable in your
report/label templates to reference them.  You can also clean up inconsistencies in your parameter
values to improve the quality of your labels and reports.  

## Introducing Context Properties

Context Properties are a feature of Inventree Part Templates that provide a simple way to include
contextual information about a part in a report.  A single Context Property may have different
values depending on the context (primarly, the category) of the part.  This is accomplished by
defining templates for the context property on catalog items (or even directly on a part) that
determine the various values desired.  For example, a part that is a resistor might include
information about resistance, wattage and tolerance (the context property's template was defined on,
or parent of, the Resistor catalog item), whereas a connector might want pin count, pitch and
current ratings (another template defined on, or parent of, the Connector item).  For any one
context property you can define custom templates on any catalog item, and even directly on a part.

In short, it's a way to define a name to use in your reporting templates, which then uses the part
to find the best template available for that part, which in turn defines the information to include
in the report.  A bit confusing at first, having templates referring to templates, but it's
surprisly easy to use and quite capable.

Pulling this all together in a simple example, let's say you have already created a context property
called `part_details`.  You can reference this property in your labels and reports just like any
other template property (as a property of `part_parameters`):

```html
<div class='category'>
  {{ part_templates.part_details }}
</div>
```

When you created the `part_details` context property, you defined a default
template value (optional, but highly recommended).  This is used when no contextual template can be
found for the part, so that the report still has usable content.  A default template might be:

```
{{ part.name }} ({{ part.ipn }}): {{ category.name }}
```

When you run your report, `{{ part_templates.part_details }}` will resolve to `{{ part.name }} ({{
part.ipn }}): {{ category.name }}` which in turn will process that template and result in something like this:

```
MFK3293C99-3Q (C19239): Resistor
```

Where this gets much more interesting is when you define templates for these context properties on
different catalog items in your InvenTree database.  You can add template values on catalog entries,
and even directly on parts, to supply detailed contextual templates for those parts.  You have full
access to all the properties of `part`, `category`, `parameter` and `stock` (if doing a stock
report/label, else it is empty) in the context property template.  When a context property is used,
the "closest" template is used (starting with the part, then walking up the catalog heirarchy,
and if none found the default template).

For example, let's say your catalog has an entry called "Integrated Circuits" and a child called
"Buffers".  You can add a `part_details` template on "Integrated Circuits" to get the "Number of
Gates" property (`{{ parameter|item:"Number of Gates" }}`), but have none on the "Integrated
Circuits / Buffers".  When the report is run, it checks first on the part (which has no
`part_details` template), then it checks "Buffers" (also none), and then it finds it on "Integrated
Circuits" and it returns the "Number of Gates" property on the part.  Of course this can include
content in the template, including conditionals and multiple parameters (it is a full
InvenTree/Django Templates template).

Similar to other template usage, any value that isn't found (such as a property not on a part) will
be ignored (blank result).  This makes it nice for defining templates higher up in the catalog
heirarchy that might reference properties that don't existing on all the children.

## Installation

Inventree Part Templates is
[installed](https://docs.inventree.org/en/stable/extend/plugins/install/) like most plugins.  Verify that plugins are enabled by visiting the `Settings / PluginS settings / Plugins`
page, and make sure the settings for `Enable URL integration`, `Enable app integration`, and `Check
plugins on startup` (if using Docker containers) are all enabled.

Then install using your preferred method.  The easiest methods are:

- Visit `Settings / Plugin Settings / Plugins` page in the management console and add the package
  name and path.
- Or, edit your `inventree_data/plugins.txt` file and add the package path.  Restart InvenTree for the
  package to be downloaded and installed.

> Use the project package name `https://github.com/cmidgley/inventree-part-templates.git`.  Once the
> documentation is complete the project will be released to the Python Repository `PyPI`, allowing the simple
> `inventree-part-templates` name to be used.  Until then, the GitHub link should be used, which
> is fully compatible with `PIP` and `plugins.txt`.

Once installed, verify that installation worked by checking the `Settings / Plugin settings /
Plugins` page.  There should be no errors from plugins at the bottom of the page, and the plugin 
`PartTemplatesPlugins` should be listed.  

# Plugin settings

The first step is to figure out what context properties you would like to start with.  You can have
up to five context properties (if you need more, open a GitHub issue).  It is common to have a part
description and a category property, and it comes with both of these defaulted.  You can remove or
edit these as you wish.  

> The reason a category context property is commonly used is because sometimes the category name needs to show
> the parent for it to make sense, such as "Capacitor / Aluminum" but other times it is unnecessary
> such as "Passive / Resistor".  The default category context property is `<parent category> / <part
> category>`.

Visit the `Settings / Plugin settings / Plugins` page to set up the context properties as well as
settings for rights to manage templates:

<img alt="InvenTree Part Templates Settings page"
src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/settings.png">

The first two fields control access rights to seeing and editing the templates on Category and Part
pages.  If both rights are disabled (edit and view) then the Part Templates panel will not be
included on the page.

The remaining ten fields are for definining the name and default template for up to five context properties.

## Using in labels and reports

With the plugin installed and some context properties defined, we can now update our reports and
labels to use them.  At this point they will just have the values from the default template, but as
category and part specific templates are added, they will automatically change their content
accordingly.  By adding them to your labels and reports now, you can tune and adjust your context
property templates to meet your usability and sizing requirements.

It is very simple to adjust a template to use context properties.  Simply open your template in any
text editor and use the syntax `{{ part_templates.<your_context_property_name> }}` and then upload
it to your label or report.  

Now you should be able to print your report or label, such as to the InvenTree PDF Label Printer to
see it on the screen and see the default template for your context property work.

## Context templates

The next step is to adjust the template value so that it is contextually appropriate.  This is
usually done on Catalog items, but can be done on individual parts as well.  For example, if you
have the catalog structure `Electronics / Passives / Capacitors / Aluminum`, you might want a
context template on `Capacitors` so you can have values specific to capacitors, but is shared across
all the different types of capacitors (Aluminum, Tantalum, MLCC, etc.)

On the Part and Category pages, assuming you have rights to see and edit the Part Templates (see
[Plugin Settings](#plugin-settings)), you should see a new "Part Templates" panel.  On Part
templates, you will see the following:

<img alt="InvenTree Part Templates Panel"
src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/part-templates-panel.png">

This panel includes the context properties, the value that each property will resolve to when the
template is applied on this specific part, and the template that is being used (including if
inherited) for this part.


When looking at a Catalog item, you don't have the value, because there is no part directly
associated with a catalog item:

<img alt="InvenTree Catalog Templates Panel"
src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/catalog-templates-panel.png">

Use the edit buttons on the right (edit, delete) to adjust the templates for this specific catalog /
part template.

## Template context variables and filters

The context templates are standard InvenTree/Djago templates, and support several context variables
and a few new filters. The context variables are:

- `part`: The current report/label [part](https://docs.inventree.org/en/stable/report/context_variables/#part)
- `category`: The current [part category](https://docs.inventree.org/en/stable/report/context_variables/#part-category)
- `parameters`: A shorthand for `part.parameters`
- `stock`: The current [stock
  item](https://docs.inventree.org/en/stable/report/context_variables/#stock), if being reported on.
  If not, such as a part report where there is no specific stock, this will be empty.  Use `{% if
  stock %}` if needing to check for availability.

### Context property template filters

The following filters are available on context property templates (though can be accessed by loading
with `{% load part_templates %}` in your labels/reports):

- `item:"<name>`: Retreives a property name from a dictionary, and [scrubs](#parameter-scrubbig) it
  is filters exist.  `{{ parameters|item:"Rated Voltage" }}`
- `value:"<name>`: Retreives a propery name from a dictionary, without any scrubbing.
- `scrub:"<name>"`: [Scrubs](#parameter-scrubbing) the prior string using a filter.  `{{
  part.name|scrub:"MPN" }}`

Some examples:

- Resistor description: `{{ parameters|item:"Resistance" }} {{ parameters|item:"Rated Power" }} {{
  parameters|item:"Tolerance" }} {{ parameters|item:"Mounting Type" }} {{ parameters|item:"Package
  Type" }}`
- Resistor short category: `RES`
- Capacitor description: `{{ parameters|item:"Capacitance"}} {{parameters|item:"Tolerance"}} {{
  parameters|item:"Rated Voltage" }} {{ parameters|item:"Mounting Type" }} {{
  parameters|item:"Package Type" }}`
- Capacitor short category: `CAP`
- Capacitor / Tantalum short category: `CAP TANT`
- Conditional example: `{{ parameters|item:"Supply Voltage" }} {% if not parameters|item:"Supply
  Voltage" %}{{ parameters|item:"Input Voltage" }} {% endif %} {{ parameters|item:"Type" }}`

# Parameter scrubbing

Parameters on parts are convienent, but often not very consistent.  This is especially true when
automatically importing parts and parameters from supplies such as DigiKey, Mouser and LCSC.  For
example, a parameter of "Mounting Type" might be "SMT", "SMD", "Surface Mount" or even "[Brick
Nogging](https://www.eevblog.com/forum/chat/where-does-all-the-weird-chinese-component-terminology-come-from/msg4313581/#msg4313581)"!

Parameter scrubbing is a way to cleanse properties, using [Regular
Expressions](https://en.wikipedia.org/wiki/Regular_expression).  The cleansing does not change the
property value in the database, so there is no risk of accidential loss of information by scrubbing.
It is used only for labels/reports, and only when you use the `item` or `scrub`
[filters](#context-property-template-filters).

The file
[part_templates.yaml](https://github.com/cmidgley/inventree-part-templates/blob/main/inventree_part_templates/part_templates.yaml)
defines a collection of filters organized by names (which are usually the same as a part's property
name), followed by a list of regular expression filters and replacement strings.  The default file
provided is based on property names used by [InvenTree Part
Import](https://github.com/30350n/inventree_part_import) using a configuration similar to [this
one](https://github.com/30350n/inventree_part_import_config).  You can specify your own template
file using the environment variable `PART_TEMPLATES_CONFIG_FILE`, such as in your `.env` file:

```
PART_TEMPLATES_CONFIG_FILE=./inventree-data/part_templates.yaml
```

Here is a simple example of filtering `Brick Nogging` and `Surface Mount` to be `SMD`:

```yaml
filters:
  "Mounting Type":
    - pattern: "^Brick .*"
      replacement: "SMD"
    - pattern: "^Surface Mount.*"
      replacement: "SMD"
```

While the `item:"<Property Name>"` filter automatically applies the name of the property to find the
filter, you can also use `scrub:"<Any Name>"` to scrub a string.  For example, you might define a
filter called `MPN` like this:

```yaml
filters:
  "MPN":
    # remove everything after a comma
    - pattern: "^\\s*([^,\\s]*).*"
      replacement: "\\1"
```

And then in your template use `{{ part.name|scrub:"MPN" }}` to apply the filter to the string
resulting from `part.name`.  In this case, it the MPN has a comma in it, everything following the
comma is removed.

There is also a `_GLOBAL` filter category, which is applied automatically on any scrubbed value.
For example:

```yaml
  "_GLOBAL":
    # currently, InvenTree does not handle reporting with chinese characters (they
    # become spaces).  Until that is fixed, this rule removes them
    - pattern: "[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]"
      replacement: ""
```


# Example labels

See the [example
labels](https://github.com/cmidgley/inventree-part-templates/tree/main/example_labels) folder for
some examples labels made for the Brother QL-810W label printer.  These labels are designed to use
29mm endless tape, and have three sizes:

- `inventree-label-part-29mm`: A full width label with long descriptions and detailed category
  names.  Set the label width to 52 and height to 27 in the part label settings.
- `inventree-label-part-16mm`: A narrow and long label, such as for placing on the edge of a
  container.  Has a horizontal cut line since it has to be manually cut (if you use 12mm endless
  tape, it would be a simple change to this label).  Set the label width to 60 and height to 28.
- `inventree-label-part-smdbox`: A very small label, sized to fit on those small, spring-hinged,
  modular ["WENTAI"](https://www.adafruit.com/product/427) boxes.  Great example of the need for
  short category names.  Set the label width to 15 and height to 26.

  > The label width sets the cutting point of the label, and the height affects the scaling of the
  > label.  A smaller height makes the label larger, and these sizes have been selected for a clean
  > fit. 

  These labels assume the following context properties are being used:
  - `description`: A long contextual part description.
  - `short-desc`: A shorter version of the part description, for the smaller labels.
  - `category`: A descriptive category name
  - `short-cat`: A very short category, maximum 6 characters per word, maximum two words.

Notice in these labels the use of another property `part_templates.error`.  This is set whenever the
templates are unable to be rendered, and makes it easier to debug why some templates are not
working.  A best practice is to check for `part_templates` and also `part_templates.error` similar
to the following:

```html
{% if not part_templates %}
    <div class="error">Plugin inventree-part-templates required</div>
{% elif part_templates.error %}
    <div class="error">{{ part_templates.error }}</div>
{% else %}
    ... your label here ...
{% endif %}

```
