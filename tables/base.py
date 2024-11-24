# pages/tables/base.py

import django_tables2 as tables
from core.mixins.tables import ActionsColumnMixin, ActionUrlMixin


class BaseTable(ActionsColumnMixin, ActionUrlMixin, tables.Table):
    """
    Base table that all tables in the app should inherit from.
    Provides default configurations for actions and URLs.
    """

    # Default URL namespace, can be overridden in each table
    url_namespace = None

    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-striped table-bordered"}

    def __init__(self, *args, **kwargs):
        # Auto-set URL namespace from the model if not explicitly provided
        if not self.url_namespace and hasattr(self.Meta, "model"):
            self.url_namespace = (
                f"{self.Meta.model._meta.app_label}:{self.Meta.model._meta.model_name}"
            )

        # Generate default URLs
        default_urls = self.generate_default_urls()

        # Apply user-defined URLs to override defaults where applicable
        custom_urls = getattr(self, "urls", {})
        self.urls = {
            **default_urls,
            **custom_urls,
        }  # Merge defaults with any custom settings
        
        # Merge custom actions into available actions
        self.available_actions += list(getattr(self, "urls", {}).keys())
        # Initialize the table with parent mixins
        super().__init__(*args, **kwargs)
