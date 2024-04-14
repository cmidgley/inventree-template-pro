""" 
    Custom Django template tags for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from django import template

register = template.Library()

@register.simple_tag
def package(package_name):
    return f"Package {package_name}"
