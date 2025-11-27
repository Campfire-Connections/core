from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Shared pagination defaults for API endpoints."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Consistent baseline for API viewsets:
    - authenticated by default
    - shared pagination
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination
