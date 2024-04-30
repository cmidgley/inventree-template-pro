""""
Setup script for the inventree-template-pro plugin.
"""
# -*- coding: utf-8 -*-

import os
from typing import Dict, List
import setuptools
from inventree_template_pro.version import PLUGIN_VERSION

# get a long_description using our README.md file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

def find_package_data(base_folder: str, source_folder: str) -> List[str]:
    """Recursively find all files within the base_folder / source_folder with .html extensions"""
    paths = []
    for (path, _directories, filenames) in os.walk(os.path.join(base_folder, source_folder)):
        for filename in filenames:
            if filename.endswith('.html'):
                directory = path[len(base_folder)+1:]
                full_path = os.path.join(directory, filename)
                print(f"Found {full_path}")
                paths.append(full_path)
    return paths

def add_templates_to_package_data(orig_package_data: Dict[str, List[str]], base_dir, template_dir):
    """
    Updates the existing package_data dictionary with HTML files found in base_dir / template_dir
    and add to the dictionary under [base_dir]
    """
    html_template_data = find_package_data(base_dir, template_dir)

    for file_to_add in html_template_data:
        orig_package_data['inventree_template_pro'].append(file_to_add)

    return orig_package_data


static_package_data: Dict[str, List[str]] = {
    'inventree_template_pro': [
        'template_pro.yaml',
        'example_labels/*',
        'example_reports/*'
    ]
}
package_data = add_templates_to_package_data(static_package_data, 'inventree_template_pro', 'templates/template_pro')

setuptools.setup(
    name="inventree-template-pro",

    version=PLUGIN_VERSION,

    author="Chris Midgley",

    author_email="chris@koose.com",

    description="InvenTree plugin that extends reporting with customizable part category templates",

    long_description=long_description,

    long_description_content_type='text/markdown',

    keywords="inventree inventreeplugins plugins label report part category print template",

    url="https://github.com/cmidgley/inventree-template-pro",

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
            "PartTemplatesPlugin = inventree_template_pro.template_pro_plugin:PartTemplatesPlugin"
        ]
    },
)
