# InvenTree-Part-Templates

Have you spent a ton of time and energy to get all your parts in [InvenTree](https://inventree.org)
to have detailed parameters, only to get labels (or lines in your reports) that look like this?

<img alt="C25076 | 0402WGF1000TCE" src="https://github.com/cmidgley/inventree-part-templates/blob/main/docs/default-label-example.png" style="border: black 1px solid" width="200px">

Wouldn't you rather have concise, detailed information about the part, specific to each part type,
using InvenTree parameters?

<img alt="100ohm 62.5mw 1% SMD 0402" src="https://github.com/cmidgley/inventree-part-templates/blob/main/docs/29mm-label-example.png" style="border: black 1px
solid" width="200px">

## Using InvenTree Part Templates

**InvenTree-Part-Templates** is a plugin for InvenTree that extends InvenTree label and reporting
templates.  You create new custom context properties, adjust template values for those properties as
desired based on the category of the parts, and use the `part_templates` context variable in your
report/label templates to reference them.  You can also clean up inconsistencies in your parameter
values to improve the quality of your labels and reports.  

### Context properties

Context properties are a feature of Inventree Part Templates that provide a simple way to include
contextual information about a part in a report.  A single context property may have different
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

## Current status

This project is currently operating in production and working well.  The documentation however is
still in development (this update is as of April 17, 2024).  If you try it and find any issues, or
have suggestions for improvement, please open a GitHub issue to discuss.  It is not currently on
PyPl, but does conform to the PIP install format so adding this to `plugins.txt` (or via the
console) via `https://github.com/cmidgley/inventree-part-templates.git`.  

Very short set of steps:
1) Install by adding `https://github.com/cmidgley/inventree-part-templates` to `plugins.txt` and
   restart the server
2) Visit settings / Plugin settings / InvenTree Part Templates, and add whatever context properties /
   default templates you want.  
3) Visit any part or category and there should be a new Part Templates panel.  Use this panel to
   add/update/remove templates for created context properties.
4) Update your label / report templates to use the context properties via `{{ part_templates.<your
   property name> }}`


## Coming soon

- Initial setup
- Defining templates
- Template filters
- Parameter cleansing
- Samples and best practices
- Installation

<!--
### Initial setup

### Defining templates on catalog and part

### Template filters
(also load, and difference in use on context property template vs. label/report template)

### Filtering parameters with `part_templates.yaml`

* document the yaml file (and [RegEx tester recommenation](https://regex101.com/))
(also env. variable)

### Errors and best practice
* document the 'error' property
* document a recommend label/report structure to test for existance

### Example labels

## Installation



  

- **Heirarchical templates**: When a label or report is generated, the part that is
  associated with it is used to locate the "cloest" template for each context variable.  This starts
  with the part itself, then it follows the category heirarchy until it reaches the top, and finally
  defaults to a value that you specify when creating the context property.


  
  Adjust the values these context properites use for templates
  on categories (following the heirarchy) and when needed directly on parts.  Any property can be
  overridden, with or without changing others, templates used for your context properties 
  by category and even on the individual part.  For example, have resistors show resistance, wattage
  and tolerance, whereas an MCU IC might show MHz, Cores and GPIO count.  Templates are inherited
  following the InvenTree categories, simplifying the effort to configure contextual templates. 

value of these context properties
  can be built up from any property on `Part`, `Stock`, `Category`, and `Parameters`.  


- **Filter and cleanse property values**: It's a fantastic time saver using other plugins that can
  import parameters from supplies like DigiKey, Mouser and LCSC, but there are no standards on their
  content.  Sometimes it's "SMD", others it's "Surface Mount", or occasionally ["Brick Nogging"](https://www.eevblog.com/forum/chat/where-does-all-the-weird-chinese-component-terminology-come-from/#msg4313581).
  You can customize filters per parameter with a YAML file to cleanse these property values for a
  consistent label/report experience.  No changes are made to the database, these filters are only
  used for generating labels and reports.
  
For information on how to install, configure and use __inventree-part-templates__, see the plugin documentation
[documentation](https://github.com/cmidgley/inventree-part-templates/blob/main/docs/toc.md).
-->