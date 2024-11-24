""" Menu Tag. """
from django import template
from django.template.loader import render_to_string
from django.urls import ResolverMatch, resolve, reverse
from django.utils.safestring import mark_safe
from annoying.functions import get_object_or_None

from ..models.menu import Menu

register = template.Library()

@register.simple_tag
def get_route_params(url_name):
    try:
        resolver_match = resolve(url_name)
        if isinstance(resolver_match, ResolverMatch):
            return resolver_match.kwargs.keys()
    except Exception as e:
        return []


@register.simple_tag()
def dynamic_url(url_name, dynamic_params=None):
    if dynamic_params:
        return reverse(url_name, kwargs=dynamic_params)
    else:
        return reverse(url_name)



@register.inclusion_tag('partials/menu.html')
def render_menu(menu_items):
    return {"menu_items": menu_items}


@register.simple_tag(takes_context=True)
def render_top_links(context, menu_name, template_name="menu/top_links.html"):
    return render_menu(context, menu_name, template_name)


def render_menu_item(item):
    url_params = item.url_params if isinstance(item.url_params, dict) else {}
    url = reverse(item.url_name, kwargs=url_params)
    return f'<a href="{url}">{item.title}</a>'
