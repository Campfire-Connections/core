from django import template
from urllib.parse import urlencode

register = template.Library()

@register.filter
def querystring(request, key_value):
    """
    Appends or replaces a key-value pair in the query string.
    Example: {{ request|get_querystring:'page=2' }}
    """
    if not hasattr(request, "GET"):
        raise ValueError("The first argument to the querystring filter must be a request object.")

    # Split key_value into key and value
    if "=" not in key_value:
        raise ValueError("querystring filter expects 'key=value' format.")

    key, value = key_value.split("=", 1)

    # Copy existing query parameters and update with the new key-value pair
    query_params = request.GET.copy()
    query_params[key] = value

    return f"?{urlencode(query_params)}"
