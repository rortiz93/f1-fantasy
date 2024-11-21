# In yourapp/templatetags/custom_filters.py
from django import template
from decimal import Decimal
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, None)



@register.filter
def sum_points(points_dict):
    # Sum the values safely, handling missing or None values
    return sum(Decimal(points_dict.get(session, '0')) for session in ['Qualifying', 'Sprint', 'Race'])