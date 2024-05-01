

### Context Property Template Tags and Filters

The following tags and filters are available on context property templates and can be accessed by
loading with `{% load template_pro %}` in your labels/reports:

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
  of the output to the specified amount (defaults to 2 to limit output).  

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




