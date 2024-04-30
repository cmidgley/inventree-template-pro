""" 
    'replace' template tag for the inventree-template-pro plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

import re
import html

from django.utils.translation import gettext_lazy as _
from .shared import register

@register.filter()
def replace(source: str, arg: str):
    """
    Replaces a string value with another, with the filter parameter having two values (match and replace) 
    being separated by the "|" character.  If the "match" side starts with "regex:" then the match and replace
    are processed as regular expressions.  The "|" can be escaped with "\\\\|" if it is needed as a character
    in the string.  

    Examples that all add a space following a separator character:
    - {% "a,b,c"|replace:",|, " %}
    - {% "A|B|C"|replace:"\\\\||\\\\|, " %}
    - {% "one,two,three"|replace:",\\\\s*(?![,])|, " %}
    """

    # Handle escaped pipe characters and split the arguments
    parts = re.split(r'(?<!\\)\|', arg)
    parts = [part.replace('\\|', '|') for part in parts]

    if len(parts) != 2:
        return _('[replace:"{arg}" must have two parameters separated by "|"]').format(arg=html.escape(arg))

    if parts[0].startswith('regex:'):
        # Regex replacement
        pattern = parts[0][6:]
        repl = parts[1]
        return re.sub(pattern, repl, source)

    # Simple replacement
    match = parts[0]
    repl = parts[1]
    return source.replace(match, repl)
