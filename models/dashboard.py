# core/models/dashboard.py

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class DashboardLayout(models.Model):
    """
    Represents the layout configuration for a user's dashboard.
    
    Args:
        user: The user associated with the dashboard layout.
        layout: The configuration of the dashboard layout.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    layout = models.TextField()
    def __str__(self):
        return f'{self.user.username} Dashboard Layout'
