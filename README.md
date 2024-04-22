Have you carefully crafted your [InvenTree](https://inventree.org) deployment only to get labels and
reports that appear meaningless:

<img alt="C25076 | 0402WGF1000TCE"
src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/default-label-example.png"
style="border: black 1px solid" width="200px">

Or have wordy and inconsistent descriptions:

<img alt="0402WGF1000TCE Passives / Resistors 62.5mW 100Ω 50V Thick Film Resistors ±200ppm/℃ ±1% 0402 Chip Resistor - Surface Mount ROHS"
src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/detailed-label-example.png"
style="border: black 1px solid" width="200px">

Wouldn't you rather have concise, detailed information from your part's parameters?

<img alt="100ohm 62.5mw 1% SMD 0402" src="https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/29mm-label-example.png" style="border: black 1px
solid" width="200px">

# InvenTree Part Templates

**InvenTree-Part-Templates** is a plugin for InvenTree that enhances InvenTree's label and reporting
templates. You can create new custom context properties, adjust template values for those properties
based on the parts' category, and access them using standard Django template language (`{{
part_templates.my_new_property }}`) in your report and label templates for easy, consistent
reporting. Additionally, this plugin allows you to clean up inconsistencies in parameter values,
significantly improving the quality of your labels and reports.

## Introducing Context Properties

Context Properties are a feature of InvenTree Part Templates that provide a straightforward way to
include contextual information about a part in a report. A single Context Property can have
different values depending on the context of the part, such as the category. This is achieved by
defining the context property template on catalog items (or directly on a part). For example, a part
that is a resistor might include information about resistance, wattage, and tolerance, whereas a
connector might display pin count, pitch, and current ratings. You can define custom templates for
on any catalog item, and even directly on a part, for any of the defined context properties.

In short, it's a way to define a name to use in your reporting templates, which then uses the part
to find the best template, which in turn defines the information to include
in the report.  It may be a bit confusing at first, with templates referring to other templates, but
it's surprisingly easy to use and highly capable.

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
found for the part, ensuring the report still has usable content.  A default template might be:

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
access to all the properties of `part`, `category`, `parameter` and `stock` (if applicable to a stock
report/label; otherwise, it is empty) in the context property template.   When a context property is
used, the "closest" template is used, starting with the part and moving up the catalog hierarchy,
and if none is found, the default template is used.


For example, let's say your catalog has an entry called "Integrated Circuits" and a subcategory
called "Buffers." You can add a `part_details` template on "Integrated Circuits" to include the
"Number of Gates" property (`{{ parameter|item:"Number of Gates" }}`), but have none on the
"Integrated Circuits / Buffers." When the report is run, it checks first on the part (which has no
`part_details` template), then it checks "Buffers" (also none), and then it finds it on "Integrated
Circuits" and returns the "Number of Gates" property on the part. 

Similarly, any value that isn't found (such as a property not on a part) will be ignored (resulting
in a blank output). This is beneficial for defining templates higher up in the catalog hierarchy
that might reference properties that do not exist on all children.

## Installation

InvenTree Part Templates is [installed](https://docs.inventree.org/en/stable/extend/plugins/install/) like most plugins. First, verify that plugins are enabled by visiting the `Settings / Plugin Settings / Plugins` page, and ensure the `Enable URL integration`, `Enable app integration`, and `Check plugins on startup` settings (if using Docker containers) are all enabled.

Then, install the plugin using your preferred method. The easiest methods are:

- The best approach, especially when using Docker, is to edit your `inventree_data/plugins.txt` file
  to add the package name (`inventree-part-templates`). Restart InvenTree for the package to be downloaded and installed.
- Visit the `Settings / Plugin Settings / Plugins` page in the management console and install it
  from there.

Once installed, verify the installation by checking the `Settings / Plugin Settings / Plugins` page. There should be no errors from plugins at the bottom of the page, and the `PartTemplatesPlugin` should be listed.

# Plugin settings

The first step is to determine which context properties you want to start with. You can have up to five context properties (if you need more, please open a GitHub issue). Commonly, a part description and a category property are used, both of which are set as defaults. You can remove or edit these as needed.

> The reason a category context property is commonly used is that sometimes the category name needs
> to show the parent category to make sense, such as "Capacitor / Aluminum." However, other times it
> is unnecessary, such as "Passive / Resistor." A default context property template of
> `{{ category.parent.name }} / {{ category.name }}` works well for "Capacitor / Aluminum", with
> `{{ category.name }}` (or just `Resistor`) used as the template on the "Registor" category.

Visit the `Settings / Plugin Settings / Plugins` page to set up the context properties as well as the settings for rights to manage templates:

![InvenTree Part Templates Settings page](https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/settings.png)

The first two fields control access rights for viewing and editing the templates on Category and Part pages. If both rights are disabled (edit and view), then the Part Templates panel will not be included on the page.

The remaining ten fields are for defining the name and default template for up to five context properties.

## Use in Labels and Reports

With the plugin installed and some context properties defined, you can now update your reports and
labels to incorporate them. Initially, they will display values from the default template, but as
you add category- and part-specific templates, the content will automatically update to reflect
these changes. By integrating them into your labels and reports now, you can fine-tune and adjust
your context property templates to meet your usability and size requirements.

Adjusting a template to use context properties is straightforward. Simply open your template in any text editor and incorporate the syntax `{{ part_templates.<your_context_property_name> }}`. Afterward, upload it to your label or report system.

You can then print your report or label, for instance, using the InvenTree PDF Label Printer, to
view how the default template for your context property functions on the screen.

> When accessing multiple parts in your reports, such as looping through all items of a BOM, you
> must request the context for each child part to access the Context Properties on it.  See the
> [`get_context`](#context-property-template-tags-and-filters) tag for additional information.

## Context Templates

The next step is to adjust the template value so that it is contextually appropriate. This adjustment is typically made on catalog items but can also be applied to individual parts. For instance, if you have the catalog structure `Electronics / Passives / Capacitors / Aluminum`, you might want a context template on `Capacitors` that is specific to all capacitor types (Aluminum, Tantalum, MLCC, etc.), allowing shared values across these different types.

On the Part and Category pages, provided you have the rights to view and edit the Part Templates (refer to [Plugin Settings](#plugin-settings)), you will see a new "Part Templates" panel. For Part templates, the panel will display as follows:

![InvenTree Part Templates Panel](https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/part-templates-panel.png)

This panel shows the context properties, the values each property will resolve to when the template is applied to a specific part, and the template currently in use (including any inherited templates).

When you view a Catalog item, the template values column is not included:

![InvenTree Catalog Templates Panel](https://github.com/cmidgley/inventree-part-templates/raw/main/README-images/catalog-templates-panel.png)

Use the edit buttons on the right (edit, delete) to modify the templates for this specific catalog
or part template.

## Template Context Variables and Filters

The context templates are standard InvenTree/Django templates and support several context variables along with a few new filters. The context variables include:

- `part`: The current report/label [part](https://docs.inventree.org/en/stable/report/context_variables/#part)
- `category`: The current [part category](https://docs.inventree.org/en/stable/report/context_variables/#part-category)
- `parameters`: A shorthand for `part.parameters`
- `stock`: The current [stock item](https://docs.inventree.org/en/stable/report/context_variables/#stock), if being reported on. If there is no specific stock item, such as in a part-only report, this variable will be empty. Use `{% if stock %}` to check for stock availability.

These variables facilitate dynamic content generation in templates, enhancing the adaptability and relevance of your reports and labels.

### Context Property Template Tags and Filters

The following tags and filters are available on context property templates and can be accessed by
loading with `{% load part_templates %}` in your labels/reports:

__Filters:__

- `item:"<name>"`: Retrieves a property name from a dictionary and [scrubs](#parameter-scrubbing) it if filters exist. Example: `{{ parameters|item:"Rated Voltage" }}`
- `value:"<name>"`: Retrieves a property name from a dictionary without any scrubbing.
- `scrub:"<name>"`: [Scrubs](#parameter-scrubbing) the associated string using a filter. Example:
  `{{ part.name|scrub:"MPN" }}`
- `replace:"<match>|<replace>"`: Replaces any matching characters in the string with the replacement
  string.  For example, to allow word breaks on a string like "R100,R103,R202,R208" you can use
  `replace:",|, "` to get "R100, R103, R202, R208".  You can escape `|` with `\|` if a vertical bar
  is needed.  Optionally can use regular expressions with `replace:"regex:<match>|<replace>`.  For
  example, using `{% ",\s*(?![,])|, " %}` will replace all "," followed by any number of space with
  ", ".
- `show_properties|<optional-depth>`: Will output any value, such as an object like `Part`, as
  nicely formatted HTML to make it easier to find and understand available properties on any
  template variable.  If a number is specified for `<optional-depth>` then it will limit the depth
  of the output to the specified amount (defaults to 2 to limit output).  Can specify `*` to output
  everything (`part|show_properties|*`).

The following are some examples of using context parameter templates with filters:

- **Resistor description**: `{{ parameters|item:"Resistance" }} {{ parameters|item:"Rated Power" }} {{ parameters|item:"Tolerance" }} {{ parameters|item:"Mounting Type" }} {{ parameters|item:"Package Type" }}`
- **Resistor short category**: `RES`
- **Capacitor description**: `{{ parameters|item:"Capacitance" }} {{ parameters|item:"Tolerance" }} {{ parameters|item:"Rated Voltage" }} {{ parameters|item:"Mounting Type" }} {{ parameters|item:"Package Type" }}`
- **Capacitor short category**: `CAP`
- **Capacitor/Tantalum short category**: `CAP TANT`
- **Conditional example**: `{{ parameters|item:"Supply Voltage" }} {% if not parameters|item:"Supply
  Voltage" %}{{ parameters|item:"Input Voltage" }} {% endif %} {{ parameters|item:"Type" }}`

__Tags:__

- `get_context <part ID> as <variable>`: Gets the context properties for part based on the part `pk`
  (primary key, or ID).  For example, when looping through parts in a BOM report, you might use a
  template section like this:

  ```
  {% for line in bom_items.all %}
  <tr>
      {% get_context line.sub_part.pk as part_context %}
      <td>{{ line.sub_part.full_name }}</td>
      <td>{% decimal line.quantity %}</td>
      <td>{% part_context.description %}</td>
      <td>{% part_context.category %}</td>
  </tr>
  {% endfor %}
  ```

# Parameter Scrubbing

Parameters on parts are convienent, but often not very consistent.  This is especially true when
automatically importing parts and parameters from supplies such as DigiKey, Mouser and LCSC.  For
example, a parameter of "Mounting Type" might be "SMT", "SMD", "Surface Mount" or even "[Brick
Nogging](https://www.eevblog.com/forum/chat/where-does-all-the-weird-chinese-component-terminology-come-from/msg4313581/#msg4313581)"!

Parameter scrubbing is a way to cleanse properties, using [Regular
Expressions](https://en.wikipedia.org/wiki/Regular_expression).  The cleansing does not change the
property value in the database, so there is no risk of accidential loss of information by scrubbing.
It is used only to resolve templates for labels/reports, and only when you use the `item` or `scrub`
[filters](#context-property-template-filters).

The file
[part_templates.yaml](https://github.com/cmidgley/inventree-part-templates/blob/main/inventree_part_templates/part_templates.yaml)
defines a collection of filters organized by names (which are usually the same as a part's property
name), followed by a list of regular expression filters and replacement strings.  The default
`part_templates.yaml` file
provided with the plugin is based on property names used by [InvenTree Part
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
resulting from `part.name`.  In this case, if the MPN has a comma in it, everything following the
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

# Example Labels

See the 
[example labels](https://github.com/cmidgley/inventree-part-templates/tree/main/inventree_part_templates/example_labels)
folder for
various labels, designed for the Brother QL-810W label printer wiht 29mm endless tape.  They all
inherit the size of the label from settings, so to some degree will auto-scale to other printers and
tape sizes.

- `inventree-label-part-large`: This is a full-size label with QR code, long descriptions and
  detailed category names across multiple lines.  The label width likely should be 50mm or wider.
- `inventree-label-part-narrow-16mm`: This narrow and long label is ideal for placing on the edge of a
  container. It has a QR-code on the left and descriptive details on the right, and features a horizontal cut line for manual cutting. Try a label width to 50+mm.
- `inventree-label-part-smdbox`: A very small label, perfectly sized for small, spring-hinged,
  modular ["WENTAI"](https://www.adafruit.com/product/427) boxes. This label is an excellent example
  of the need for short category names. Set the label width to 15 to fit the boxes, and cut them
  using the printed cut-line.
- `inventree-label-part-gridfinity`: A 12mm x 36mm label sized to fit
  [Gridfinity](https://gridfinity.xyz/) single-unit 12mm labels (such as those generated using the
  [Fusion 360 Gridfinity
  Generator](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7197558650811789)).  Gridfinity
  uses about 40mm width for labels (34mm in settings).

> Brother labels have margins of about 3mm on the left and right edges, and 1.5mm on the top and
> bottom.  When setting the label size in settings, the width will control the cutting length (not
> including margins, so 50mm will be 56mm cut), but height changes scaling of the content, not the
> size!  Given the 1.5mm per top/bottom margin, assuming a label size of 29mm, set the label height
> in settings to to 26mm (29mm - 3mm margins).

> When designing labels to a particular height (such as when using borders as cut-lines to cut the
> label), set your label height correctly (see prior paragrap), and in your label template set the
> containing DIV to a height of your desired height, less 1.5mm (for the top margin) and use a thin
> border on the bottom to draw a cut line.  The distance from the factory-edge to the cut-line will
> then match your desired height.  For example, for a 29mm label that wants to be used for a 12mm
> cut label will set the label height in settings to 26mm, and the DIV height to 10.5mm.

  These labels utilize the following context properties:

  - `description`: A long contextual part description.
  - `short-desc`: A shorter version of the part description, suitable for the smaller labels.
  - `category`: A descriptive category name.
  - `short-cat`: A very short category, limited to a maximum of 6 characters per word and up to two words.


# Example reports

See the 
[example reports](https://github.com/cmidgley/inventree-part-templates/tree/main/inventree_part_templates/example_reports)
folder for example reports.  These reports use the `{% get_context %}` tag lookup context
information on the child parts in order to display detailed information about multiple parts in a
single report.


# Best practice for template error detection

A best practice is to check for errors in the template, so that you can see descriptive errors in your
report/labels when there is a problem with a template.  This is accompished by using the
`part_templates.error` context property.  See the example labels and reports, where you will find
logic similar to the following:

```html
{% if not part_templates %}
    <div class="error">Plugin inventree-part-templates required</div>
{% elif part_templates.error %}
    <div class="error">{{ part_templates.error }}</div>
{% else %}
    ... your report/label template here ...
{% endif %}
```
