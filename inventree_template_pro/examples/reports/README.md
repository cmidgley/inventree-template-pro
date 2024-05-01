

# Example reports

See the 
[example reports](https://github.com/cmidgley/inventree-template-pro/tree/main/inventree_template_pro/example_reports)
folder for example reports.  These reports use the `{% get_context %}` tag lookup context
information on the child parts in order to display detailed information about multiple parts in a
single report.


# Best practice for template error detection

A best practice is to check for errors in the template, so that you can see descriptive errors in your
report/labels when there is a problem with a template.  This is accompished by using the
`template_pro.error` context property.  See the example labels and reports, where you will find
logic similar to the following:

```html
{% if not template_pro %}
    <div class="error">Plugin inventree-template-pro required</div>
{% elif template_pro.error %}
    <div class="error">{{ template_pro.error }}</div>
{% else %}
    ... your report/label template here ...
{% endif %}
```
