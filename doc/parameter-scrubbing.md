<p align="center"><img src="images/InvenTree Template Pro Logo.png" alt="InvenTree Template Pro
Logo" width="80px"></p>

<h3 align="center">

[InvenTree Template Pro](README.md)

</h3>


### Parameter Scrubbing

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
[template_pro.yaml](https://github.com/cmidgley/inventree-template-pro/blob/main/inventree_template_pro/template_pro.yaml)
defines a collection of filters organized by names (which are usually the same as a part's property
name), followed by a list of regular expression filters and replacement strings.  The default
`template_pro.yaml` file
provided with the plugin is based on property names used by [InvenTree Part
Import](https://github.com/30350n/inventree_part_import) using a configuration similar to [this
one](https://github.com/30350n/inventree_part_import_config).  You can specify your own template
file using the environment variable `TEMPLATE_PRO_CONFIG_FILE`, such as in your `.env` file:

```
TEMPLATE_PRO_CONFIG_FILE=./inventree-data/template_pro.yaml
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