# InvenTree-Part-Templates


Have you spent a ton of time and energy to get all your parts in [InvenTree](https://inventree.org)
to have detailed parameters, only to get labels (or lines in your reports) that look like this?

<img alt="C25076 | 0402WGF1000TCE" src="docs/default-label-example.png" style="border: black 1px solid" width="200px">

Wouldn't you rather have concise, detailed information about the part, specific to each part type,
using InvenTree parameters?

<img alt="100ohm 62.5mw 1% SMD 0402" src="docs/29mm-label-example.png" style="border: black 1px
solid" width="200px">

**InvenTree-Part-Templates** is a plugin for InvenTree that extends InvenTree label and reporting
templates with the following capabilities:

- **Customizable context properties**: Create your own context properties to use in reports and
  labels, such as "part_parameters", "short_category_name".  The value of these context properties
  can be built up from any property on `Part`, `Stock`, `Category`, and `Parameters`.  

- **Category and part customization**: Adjust the templates used for your context properties 
  by category and even on the individual part.  For example, have resistors show resistance, wattage
  and tolerage, whereas an MCU IC might show MHz, Cores and GPIO count.  Templates are inherited
  following the InvenTree categories, simplifying the effort to configure contextual templates. 

- **Simplified and consistent reporting**: Easily reference templates within your reports or labels
  using standard Django template placeholders/  For example, use `{{ part_templates.part_description
  }}` to reference the `part_description` context property, and have it automatically filled in
  based on the category/part templates.

- **Easy to configure templates with integrated panel**: Categories and parts get a new `Parts
  Template` panel in the user interface (with options to show/hide based on rights and preferenes)
  to see the current templates for each context property, if it's inherited from a parent category
  or not, and the ability to edit or remove the template.

- **Filter and cleanse property values**: It's a fantastic time saver using other plugins that can
  import parameters from supplies like DigiKey, Mouser and LCSC, but there are no standards on their
  content.  Sometimes it's "SMD", others it's "Surface Mount", or occasionally ["Brick Nogging"](https://www.eevblog.com/forum/chat/where-does-all-the-weird-chinese-component-terminology-come-from/#msg4313581).
  You can customize filters per parameter with a YAML file to cleanse these property values for a
  consistent label/report experience.  No changes are made to the database, these filters are only
  used for generating labels and reports.
  
For information on how to install, configure and use __inventree-part-templates__, see the plugin documentation
[documentation](docs/toc.md).