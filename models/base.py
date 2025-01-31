# core/models/base.py

from django.db import models
from django.urls import reverse


class BaseModel(models.Model):
    class Meta:
        abstract = True

    def menu_config(self, user):
        menu = []
        
        if user.is_admin:
            change_status = {'label': 'Change Status', 'url': '#', 'icon': 'fa-check-circle'}
            clone = {'label': 'Clone', 'url': '#', 'icon': 'fa-copy'}
            edit = {'label': 'Edit', 'url': '#', 'icon': 'fa-edit'}
            assign = {'label': 'Assign Faculty', 'url': '#', 'icon': 'fa-fa-arrow-right'}

        add_comment = {'label': 'Add Comment', 'url': '#', 'icon': 'fa-comment'}
        printt = {'label': 'Print', 'url': '#', 'icon': 'fa-print'}
        
        
