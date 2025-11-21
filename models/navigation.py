from django.conf import settings
from django.db import models


class NavigationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="navigation_preference",
        on_delete=models.CASCADE,
    )
    favorite_keys = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_favorite(self, key):
        favorites = set(self.favorite_keys or [])
        favorites.add(key)
        self.favorite_keys = list(favorites)
        self.save(update_fields=["favorite_keys", "updated_at"])

    def remove_favorite(self, key):
        favorites = set(self.favorite_keys or [])
        favorites.discard(key)
        self.favorite_keys = list(favorites)
        self.save(update_fields=["favorite_keys", "updated_at"])
