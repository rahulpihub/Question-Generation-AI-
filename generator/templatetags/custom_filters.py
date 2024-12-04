# generator/templatetags/custom_filters.py

from django import template
import os

register = template.Library()

@register.filter(name='basename')
def basename(value):
    """
    Custom filter to get the basename of a file path.
    """
    return os.path.basename(value)
