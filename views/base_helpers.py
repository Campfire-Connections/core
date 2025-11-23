# core/views/base_helpers.py

from django_tables2 import RequestConfig


def build_tables_from_config(request, tables_config, default_paginate=10):
    """
    Instantiate django-tables2 tables from a configuration dictionary.

    Expected config format:
        {
            "table_name": {
                "class": TableClass,
                "queryset": qs,
                "paginate_by": 10,  # optional
            },
            ...
        }
    """

    initialized_tables = {}

    for table_key, cfg in tables_config.items():
        table_class = cfg["class"]
        queryset = cfg["queryset"]
        paginate_by = cfg.get("paginate_by", default_paginate)

        # Allow lazy callables for queryset (like lambdas in ShowView)
        if callable(queryset):
            queryset = queryset()

        table = table_class(queryset, request=request)

        # Configure pagination
        if paginate_by:
            RequestConfig(request, paginate={"per_page": paginate_by}).configure(table)
        else:
            RequestConfig(request).configure(table)

        initialized_tables[table_key] = table

    return initialized_tables
