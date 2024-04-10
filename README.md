# InvenTree-Part-Templates

**InvenTree-Part-Templates** is a plugin for InvenTree that enhances the reporting capabilities,
including regular and label reports, by introducing context variables derived from category and part
templates. This plugin allows for extensive customization based on part-specific attributes and
category hierarchies, enabling users to create highly tailored template definitions.  For example,
you might have a label that uses "{{ part_templates.description }}" that resolves to "1.1K 1% 62.5mW
0402" on a resistor, but "10pF 65V Tant 1206" for a capacitor, all based on the part category and
part properties.

## Features

- **Template Customization**: Define multiple template names, each supporting its own set of
  inherited templates. This feature allows multiple templates to be customized, such as for short
  and long parametric part descriptions, and accurate category names without the full heirarchy.
  
- **Flexible Inheritance**: Templates are primarily defined per part category and are inherited from
  parent categories, but can be overridden on individual parts.  This makes templates easy to
  define, but also the ability to be highly precise down the the individual part.

- **Simplified and consistent reporting**: Easily reference templates within your reports or labels
  using standard Django template placeholders (`{{ part_templates.part_description }}`). The
  templates can be used on any report, including labels, any place where you access parts or stock.

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

