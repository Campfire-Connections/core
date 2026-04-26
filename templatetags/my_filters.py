# pages/templatetags/my_filters.py

import logging

from django import template
from django.template.defaultfilters import title
from django.urls import reverse
from django.utils.safestring import mark_safe
import inflect

register = template.Library()
p = inflect.engine()
logger = logging.getLogger(__name__)


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
        return ""

    try:
        plural_word = p.plural(str(word))
        if capitalize:
            plural_word = plural_word.capitalize()
        return plural_word
    except Exception:
        logger.debug("Unable to pluralize word: %r", word, exc_info=True)
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


@register.filter(name="contains")
def contains(collection, item):
    try:
        return item in collection
    except TypeError:
        return False


@register.filter(name="nbsp")
def nbsp(value):
    """
    Replace regular spaces with non-breaking spaces to keep labels on one line.
    """
    if value is None:
        return ""
    return mark_safe(str(value).replace(" ", "&nbsp;"))
