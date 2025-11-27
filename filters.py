"""
Base filterset utilities for DRF and django-filter integration.
"""

import django_filters


class BaseFilterSet(django_filters.FilterSet):
    """
    Extend to add common filters/pagination semantics.
    """

    ordering = django_filters.OrderingFilter(fields=("id",))
