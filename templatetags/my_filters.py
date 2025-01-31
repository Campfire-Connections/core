# pages/templatetags/my_filters.py

from django import template
from django.template.defaultfilters import title
from django.urls import reverse
import inflect

register = template.Library()
p = inflect.engine()


@register.simple_tag
def generate_url(url_name, **kwargs):
    return reverse(url_name, **kwargs)


@register.filter(name="pluralize_custom")
def pluralize_custom(value, word):
    """
    Pluralize the given word based on the value.
    Usage: {{ value|stringname_pluralize:"word" }}
    Example: {{ 5|stringname_pluralize:"item" }} -> "items"
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return word

    return p.plural(word) if value != 1 else word


@register.filter
def pluralize_word(word, capitalize=False):
    if not isinstance(word, str):
        raise ValueError("Input to pluralize_word must be a string.")

    try:
        plural_word = p.plural(word)
        if capitalize:
            plural_word = plural_word.capitalize()
        return plural_word
    except Exception as e:
        # Log the exception for debugging
        print(f"Error in pluralize_word: {e}")
        return word  # Fallback to the original word if an error occurs


@register.filter(name="singlize_custom")
def singlize_custom(word):
    """
    Convert a plural word to its singular form.
    Usage: {{ word|stringname_singlize }}
    Example: {{ "buses"|stringname_singlize }} -> "bus"
    """
    return p.singular_noun(word) or word


@register.filter(name="int")
def int_filter(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


@register.filter(name="spacify")
def spacify(value):
    return value.replace("_", " ")
