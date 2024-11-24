# core/models/settings.py

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

class Setting(models.Model):
    # Setting key and value
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    # Global, Organization, or Faction level setting
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Optional: You can add metadata like when the setting was created or modified
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.key}: {self.value} for {self.content_object}"
