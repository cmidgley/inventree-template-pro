# -*- coding: utf-8 -*-

import setuptools

from inventree_part_templates.version import PLUGIN_VERSION

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name="inventree-part-templates",

    version=PLUGIN_VERSION,

    author="Chris Midgley",

    author_email="chris@koose.com",

    description="InvenTree plugin that extends reporting with customizable part category templates",

    long_description=long_description,

    long_description_content_type='text/markdown',

    keywords="inventree label report part category print template",

    url="https://github.com/cmidgley/inventree-part-templates",

    license="MIT",

    packages=setuptools.find_packages(),

    install_requires=[],

    setup_requires=[
        "wheel",
        "twine",
    ],

    python_requires=">=3.9",

    entry_points={
        "inventree_plugins": [
            "PartTemplatesPlugin = inventree_brother.part_templates_plugin:PartTemplatesPlugin"
        ]
    },
)
