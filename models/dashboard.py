# core/models/dashboard.py

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class DashboardLayout(models.Model):
    """
    Stores per-user dashboard preferences (layout JSON + hidden widget keys) scoped to a portal key.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="dashboard_layouts"
    )
    portal_key = models.CharField(max_length=64, default="default")
    layout = models.TextField(blank=True)
    hidden_widgets = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "portal_key")

    def __str__(self):
        return f"{self.user.username} - {self.portal_key} Dashboard Layout"
