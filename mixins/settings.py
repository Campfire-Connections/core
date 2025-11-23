# core/mixins/settings.py

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

from core.models.settings import Setting

class SettingsMixin:
    
    def get_fallback_chain(self):
        """
        Define the fallback chain for settings lookup.
        Override this method in your models to customize fallback behavior.
        Returns a list of methods or attributes to check in order.
        """
        return []  # Default to no fallback chain

    def get_setting(self, key, default=None):
        """
        Retrieve the setting by following the fallback chain.
        Start with the current model instance, and if the setting is not found,
        follow the fallback chain.
        """
        # First, try to get the setting at the current level (self)
        setting_value = self._get_model_setting(key)
        if setting_value is not None:
            return setting_value

        # If setting not found, follow the fallback chain
        for fallback_source in self.get_fallback_chain():
            if callable(fallback_source):
                # If it's a method, call it to get the next object
                next_obj = fallback_source()
            else:
                # Otherwise, treat it as an attribute name
                next_obj = getattr(self, str(fallback_source), None)

            if next_obj:
                # Try to get the setting from the fallback object
                setting_value = next_obj._get_model_setting(key)
                if setting_value is not None:
                    return setting_value

        # Fallback to global settings
        global_setting = Setting.objects.filter(content_type=None, object_id=None, key=key).first()
        if global_setting:
            return global_setting.value

        # Finally, return the default value if no setting was found
        return default

    def _get_model_setting(self, key):
        """Helper method to get the setting for the current model instance."""
        content_type = ContentType.objects.get_for_model(self.__class__)
        setting = Setting.objects.filter(content_type=content_type, object_id=self.pk, key=key).first()
        return setting.value if setting else None

