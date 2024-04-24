""" 
    'stocklist' template tag for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from django import template
from part.models import Part
from stock.models import StockItem
from stock.models import StockLocation
from django.utils.translation import gettext_lazy as _
from typing import List
from stock.models import StockItem


# define register so that Django can find the tags/filters
register = template.Library()


def _get_stock_items(part, location_name=None, min_on_hand=None):
    """
    Fetch all StockItems for a given part and optionally filter by StockLocation or its descendants,
    and by a minimum quantity on hand.

    Args:
        part (Part): The Part instance for which to find StockItems.
        location_name (str, optional): The name of the StockLocation to filter by. Defaults to None.
        min_on_hand (int, optional): The minimum quantity that must be on hand. Defaults to None.

    Returns:
        QuerySet: A queryset of StockItem instances.
    """
    # Start with all stock items for the given part
    stock_items = StockItem.objects.filter(part=part)

    # Filter by minimum quantity on hand if specified
    if min_on_hand is not None:
        stock_items = stock_items.filter(quantity__gte=min_on_hand)

    # If a location name is provided, further filter the stock items
    if location_name:
        try:
            # Get the StockLocation by name
            location = StockLocation.objects.get(name=location_name)
            # Get all descendants including the location itself
            locations = location.get_descendants(include_self=True)
            # Filter stock items by these locations
            stock_items = stock_items.filter(location__in=locations)
        except StockLocation.DoesNotExist:
            # If no such location exists, return an empty queryset
            return StockItem.objects.none()
    return stock_items

@register.simple_tag()
def stocklist(part: Part | int, min_quantity_on_hand: int, location: str) -> List[StockItem]:
    """
    Filter to get a list of stock items for a part, optionally filtering by a minimum number of
    available stock items and also limited to a location.  It returns a list of StockItem objects
    that match the criteria.  If a location is specified, it should be the extact name of a 
    location, and it will match that location and any children of that location.

    QUESTION: Shouldn't this really be about allocations?  Where did I make an allocation for
    the specific BOM?  This call is generic to a part, which has benefits, but in the use case
    of a BOM, we want to see what part(s) we allocated.

    Examples:
    - {% stocklist part as stock_list %}
    - {% stocklist list.part.pk 10 as stock_list as stock_list %}
    - {% stocklist part 0 "West Assembly Building" as stock_list %}
    """
    # get the part object if it is not already
    if isinstance(part, int):
        part = Part.objects.get(pk=part)

    if not part:
        return []

    # get the stock items for the part
    return _get_stock_items(part, location, min_quantity_on_hand)
