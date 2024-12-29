# core templatetags/string_filters.py

from django import template

register = template.Library()


@register.filter(name="underscore_to_space")
def underscore_to_space(value):
    """
    Replaces underscores with spaces in a string.
    """
    if isinstance(value, str):
        return value.replace("_", " ")
    return value  # Return the original value if it's not a string
