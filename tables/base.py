# core/tables/base.py

import logging
import django_tables2 as tables

from core.mixins.tables import ActionsColumnMixin, ActionUrlMixin

logger = logging.getLogger(__name__)


class BaseTable(ActionsColumnMixin, ActionUrlMixin, tables.Table):
    """A base table class providing enhanced functionality for Django tables.

    Serves as a foundational table class with dynamic column filtering, action management, and
    contextual rendering capabilities.

    Attributes:
        default_attrs: Default CSS classes for table styling.
        available_actions: Optional list of actions for each table row.

    Methods:
        filter_columns: Dynamically filters table columns.
        log_debug_info: Logs table initialization details in debug mode.
        get_contextual_attrs: Provides dynamic row attributes based on record context.
        render_row: Optionally customizes row rendering with contextual attributes.

    Args:
        user: The current user for contextual rendering.
        fields: Optional list of columns to display.
        attrs: Additional table attributes.
        debug_mode: Flag to enable detailed logging.
    """

    # Default table attributes
    default_attrs = {"class": "table table-striped table-bordered"}

    class Meta:
        """Metadata configuration for the base table class.

        Defines default table rendering settings, including template, CSS attributes, and
        abstract class status. Prevents direct instantiation of the base table.

        Attributes:
            template_name: The HTML template used for rendering the table.
            attrs: Default CSS classes for table styling.
            abstract: Flag to prevent direct instantiation of the base table.
        """

        template_name = "django_tables2/bootstrap4.html"
        abstract = True  # Prevent direct instantiation

    def __init__(
        self, *args, user=None, fields=None, attrs=None, debug_mode=False, **kwargs
    ):
        """
        Initialize the table with dynamic attributes and column filtering.
        """
        self.user = user  # Store the user for contextual rendering
        self.debug_mode = debug_mode

        # Apply dynamic attributes
        if attrs:
            self.Meta.attrs = {**self.default_attrs, **(attrs or {})}

        super().__init__(*args, **kwargs)

        # Dynamically filter columns if 'fields' argument is provided
        if fields:
            self.filter_columns(fields)

        # Dynamically add action columns
        if hasattr(self, "available_actions"):
            self.add_actions_column()

        if debug_mode:
            self.log_debug_info()

    def filter_columns(self, fields):
        """
        Filter table columns based on the provided fields list.
        """
        self.base_columns = {
            name: column for name, column in self.base_columns.items() if name in fields
        }

    def log_debug_info(self):
        """
        Log table initialization details for debugging purposes.
        """
        logger.info(f"Initializing table {self.__class__.__name__}")
        logger.info(f"User: {self.user}")
        logger.info(f"Columns: {list(self.base_columns.keys())}")

    def get_contextual_attrs(self, record):
        """
        Return dynamic attributes based on the context of the record.
        """
        # Example: Highlight a row based on a condition
        if hasattr(record, "status") and record.status == "active":
            return {"class": "table-success"}
        return {}
