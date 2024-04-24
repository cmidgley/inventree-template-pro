""""
Setup script for the inventree-part-templates plugin.
"""
# -*- coding: utf-8 -*-

import os
from typing import Dict, List
import setuptools
from inventree_part_templates.version import PLUGIN_VERSION

# get a long_description using our README.md file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

def find_package_data(source_folder: str, extensions: List[str] | None = None) -> Dict[str, str]:
    """Recursively find all files within the source_folder with specific extensions."""
    paths = {}
    if extensions is None:
        extensions = ['.html']
    for (path, _directories, filenames) in os.walk(source_folder):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                # Get the relative path from the source_folder, then join it with the filename
                directory = path[len(source_folder)+1:]
                full_path = os.path.join(directory, filename)
                paths.setdefault(directory, []).append(full_path)
    return paths

def add_templates_to_package_data(orig_package_data: Dict[str, List[str]], template_dir, extensions = None):
    """
    Updates the existing package_data dictionary with HTML files found in template_dir.
    Assumes template_dir is a relative path from the package root directory.
    """
    html_template_data = find_package_data(template_dir, extensions)

    # Prepend the package name to the keys found from find_package_data
    for key, files in html_template_data.items():
        full_key = f'inventree_part_templates/{key}'
        if full_key in orig_package_data:
            orig_package_data[full_key].extend(files)
        else:
            orig_package_data[full_key] = [files]

    return orig_package_data

static_package_data: Dict[str, List[str]] = {
    'inventree_part_templates': [
        'part_templates.yaml',
        'example_labels/*',
        'example_reports/*'
    ]
}
package_data = add_templates_to_package_data(static_package_data, 'inventree_part_templates/templates/part_templates')

print("Inside setup.py")
print(package_data)

setuptools.setup(
    name="inventree-part-templates",

    version=PLUGIN_VERSION,

    author="Chris Midgley",

    author_email="chris@koose.com",

    description="InvenTree plugin that extends reporting with customizable part category templates",

    long_description=long_description,

    long_description_content_type='text/markdown',

    keywords="inventree inventreeplugins plugins label report part category print template",

    url="https://github.com/cmidgley/inventree-part-templates",

    license="MIT",

    packages=setuptools.find_packages(),

    package_data=package_data,

    include_package_data=False,

    install_requires=[],

    setup_requires=[
        "wheel",
    ],

    python_requires=">=3.9",

    entry_points={
        "inventree_plugins": [
            "PartTemplatesPlugin = inventree_part_templates.part_templates_plugin:PartTemplatesPlugin"
        ]
    },
)
