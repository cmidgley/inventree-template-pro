<p align="center"><img src="../../../doc/images/InvenTree Template Pro Logo.png" alt="InvenTree Template Pro
Logo" width="80px"></p>

<h3 align="center">

[InvenTree Template Pro](../../../doc/README.md)

</h3>

### Example Labels

See the 
[example labels](https://github.com/cmidgley/inventree-template-pro/tree/main/inventree_template_pro/example_labels)
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
  uses about 36mm width for labels (30mm in settings).

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


### Best practice for template error detection

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
