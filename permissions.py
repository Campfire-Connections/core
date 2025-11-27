"""
Shared permission classes for DRF viewsets.
"""

from rest_framework import permissions


class IsAuthenticatedAndActive(permissions.IsAuthenticated):
    """
    Require authenticated and active users.
    """

    def has_permission(self, request, view):
        return super().has_permission(request, view) and getattr(
            request.user, "is_active", False
        )
