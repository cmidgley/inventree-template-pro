# InvenTree Template Pro

General documentation on installation, configuration, and usage:

- [Installation](doc/installation.md): Brief description of how to install the plugin.
- [Context Templates](doc/context-templates.md): How to use Context Templates for parts based on part categories.
- [Parameter Scrubbing](doc/parameter-scrubbing.md): How to configure parameter scrubbing to clean up imported parameter values.
- [Example reports](inventree_template_pro/example/reports) and [Example labels](inventree_template_pro/example/labels): Review examples included in this GitHub repo.

Information on each of the tags and filters provided by InvenTree Template Pro:

- [`call` tag](doc/tags/call.md): Utility tag to call any method of an object with parameters.
- [`explore` tag](doc/tags/explore.md): Explore the properties and methods of InvenTree objects in your reports.
- [`item` filter](doc/filters/item.md): Retrieve a property value from a part (or any dictionary) with automatic Parameter Scrubbing.
- [`part_context` tag](doc/tags/part-context.md): Get a part context using Context Templates for any part, such as when
  processing parts in a loop for reporting.
- [`replace` filter](doc/filters/replace.md): Helper method to replace content in a string using simple match/replace or
  more advanced with regular expressions.
- [`scrub` filter](doc/filters/scrub.md): Scrub any string based on any filter name using Parameter Scrubbing.
- [`value` filter](doc/filters/value.md): Retrieve a property value from a part (or any dictionary), without Parameter Scrubbing.