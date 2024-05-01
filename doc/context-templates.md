<p align="center"><img src="images/InvenTree Template Pro Logo.png" alt="InvenTree Template Pro
Logo" width="80px"></p>

<h3 align="center">

[InvenTree Template Pro](README.md)

</h3>

**inventree-template-pro** is a plugin for InvenTree that enhances InvenTree's label and reporting
templates. You can create new custom context properties, adjust template values for those properties
based on the parts' category, and access them using standard Django template language (`{{
template_pro.my_new_property }}`) in your report and label templates for easy, consistent
reporting. Additionally, this plugin allows you to clean up inconsistencies in parameter values,
significantly improving the quality of your labels and reports.

#### Introducing Context Properties

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
  {{ template_pro.part_details }}
</div>
```

When you created the `part_details` context property, you defined a default
template value (optional, but highly recommended).  This is used when no contextual template can be
found for the part, ensuring the report still has usable content.  A default template might be:

```
{{ part.name }} ({{ part.ipn }}): {{ category.name }}
```

When you run your report, `{{ template_pro.part_details }}` will resolve to `{{ part.name }} ({{
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



#### Plugin settings

The first step is to determine which context properties you want to start with. You can have up to five context properties (if you need more, please open a GitHub issue). Commonly, a part description and a category property are used, both of which are set as defaults. You can remove or edit these as needed.

> The reason a category context property is commonly used is that sometimes the category name needs
> to show the parent category to make sense, such as "Capacitor / Aluminum." However, other times it
> is unnecessary, such as "Passive / Resistor." A default context property template of
> `{{ category.parent.name }} / {{ category.name }}` works well for "Capacitor / Aluminum", with
> `{{ category.name }}` (or just `Resistor`) used as the template on the "Registor" category.

Visit the `Settings / Plugin Settings / Plugins` page to set up the context properties as well as the settings for rights to manage templates:

![InvenTree Part Templates Settings page](https://github.com/cmidgley/inventree-template-pro/raw/main/README-images/settings.png)

The first two fields control access rights for viewing and editing the templates on Category and Part pages. If both rights are disabled (edit and view), then the Part Templates panel will not be included on the page.

The remaining ten fields are for defining the name and default template for up to five context properties.

##### Use in Labels and Reports

With the plugin installed and some context properties defined, you can now update your reports and
labels to incorporate them. Initially, they will display values from the default template, but as
you add category- and part-specific templates, the content will automatically update to reflect
these changes. By integrating them into your labels and reports now, you can fine-tune and adjust
your context property templates to meet your usability and size requirements.

Adjusting a template to use context properties is straightforward. Simply open your template in any text editor and incorporate the syntax `{{ template_pro.<your_context_property_name> }}`. Afterward, upload it to your label or report system.

You can then print your report or label, for instance, using the InvenTree PDF Label Printer, to
view how the default template for your context property functions on the screen.

> When accessing multiple parts in your reports, such as looping through all items of a BOM, you
> must request the context for each child part to access the Context Properties on it.  See the
> [`get_context`](#context-property-template-tags-and-filters) tag for additional information.

#### Context Templates

The next step is to adjust the template value so that it is contextually appropriate. This adjustment is typically made on catalog items but can also be applied to individual parts. For instance, if you have the catalog structure `Electronics / Passives / Capacitors / Aluminum`, you might want a context template on `Capacitors` that is specific to all capacitor types (Aluminum, Tantalum, MLCC, etc.), allowing shared values across these different types.

On the Part and Category pages, provided you have the rights to view and edit the Part Templates (refer to [Plugin Settings](#plugin-settings)), you will see a new "Part Templates" panel. For Part templates, the panel will display as follows:

![InvenTree Part Templates Panel](https://github.com/cmidgley/inventree-template-pro/raw/main/README-images/template-pro-panel.png)

This panel shows the context properties, the values each property will resolve to when the template is applied to a specific part, and the template currently in use (including any inherited templates).

When you view a Catalog item, the template values column is not included:

![InvenTree Catalog Templates Panel](https://github.com/cmidgley/inventree-template-pro/raw/main/README-images/catalog-templates-panel.png)

Use the edit buttons on the right (edit, delete) to modify the templates for this specific catalog
or part template.

#### Template Context Variables and Filters

The context templates are standard InvenTree/Django templates and support several context variables along with a few new filters. The context variables include:

- `part`: The current report/label [part](https://docs.inventree.org/en/stable/report/context_variables/#part)
- `category`: The current [part category](https://docs.inventree.org/en/stable/report/context_variables/#part-category)
- `parameters`: A shorthand for `part.parameters`
- `stock`: The current [stock item](https://docs.inventree.org/en/stable/report/context_variables/#stock), if being reported on. If there is no specific stock item, such as in a part-only report, this variable will be empty. Use `{% if stock %}` to check for stock availability.

These variables facilitate dynamic content generation in templates, enhancing the adaptability and
relevance of your reports and labels.

##### TODO: Add links to the various filters