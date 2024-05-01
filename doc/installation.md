<p align="center"><img src="images/InvenTree Template Pro Logo.png" alt="InvenTree Template Pro
Logo" width="80px"></p>

<h3 align="center">

[InvenTree Template Pro](README.md)

</h3>


#### Installation

InvenTree Part Templates is [installed](https://docs.inventree.org/en/stable/extend/plugins/install/) like most plugins. First, verify that plugins are enabled by visiting the `Settings / Plugin Settings / Plugins` page, and ensure the `Enable URL integration`, `Enable app integration`, and `Check plugins on startup` settings (if using Docker containers) are all enabled.

Then, install the plugin using your preferred method. The easiest methods are:

- The best approach, especially when using Docker, is to edit your `inventree_data/plugins.txt` file
  to add the package name (`inventree-template-pro`). Restart InvenTree for the package to be downloaded and installed.
- Visit the `Settings / Plugin Settings / Plugins` page in the management console and install it
  from there.

Once installed, verify the installation by checking the `Settings / Plugin Settings / Plugins` page. There should be no errors from plugins at the bottom of the page, and the `TemplatesProPlugin` should be listed.