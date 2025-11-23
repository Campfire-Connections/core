# core/mixins/tables.py

import logging
import django_tables2 as tables
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import camel_case_to_spaces
from core.utils import is_leader_admin, is_faculty_admin, is_department_admin

logger = logging.getLogger(__name__)


class ActionUrlMixin:
    """
    Mixin to handle action URLs like 'add', 'show', 'edit', 'delete', etc., with support for
    context-based URL generation and dynamic URL configurations.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the mixin and sets up default URLs for actions. This constructor calls the
        parent class's initializer and generates the default URLs needed for the mixin's
        functionality.

        Args:
            self: The instance of the class.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        super().__init__(*args, **kwargs)
        # Set up default URLs for actions
        self.default_urls = self.generate_default_urls()

    def get_url(self, action, record=None, context=None):
        """
        Generates a URL for a specified action, optionally using a record and context for
        additional parameters. This function combines custom and default URL information, builds
        the necessary URL arguments, and attempts to reverse the URL, handling any errors that may
        occur.

        Args:
            self: The instance of the class.
            action (str): The action for which to generate the URL.
            record (optional): An optional record that may provide additional context for the URL.
            context (optional): An optional context that may provide additional parameters for the
                URL.

        Returns:
            str: The generated URL as a string, or a default placeholder if the URL cannot be
                constructed.

        Raises:
            NoReverseMatch: If the URL cannot be reversed due to an invalid name or parameters.
        """

        action_url_info = self.urls.get(action, {})
        url_name = action_url_info.get("name", f"{self.url_namespace}:{action}")
        kwargs_config = action_url_info.get("kwargs", {})

        url_kwargs = self.build_url_kwargs(kwargs_config, record, context)

        try:
            return reverse(url_name, kwargs=url_kwargs)
        except NoReverseMatch:
            if self.debug_mode:
                logger.warning(
                    f"URL reverse failed for action '{action}' with kwargs {url_kwargs}"
                )
            return "#"

    def build_url_kwargs(self, kwargs_config, record=None, context=None):
        """
        Constructs a dictionary of URL keyword arguments based on the provided configuration,
        record, and context. This function retrieves values from the context or the record,
        allowing for flexible URL generation based on nested attributes.

        Args:
            self: The instance of the class.
            kwargs_config (dict): A mapping of keys to attribute paths used to extract values.
            record (optional): An optional record from which to retrieve attribute values.
            context (optional): An optional context that may provide additional values for the URL
                kwargs.

        Returns:
            dict: A dictionary containing the constructed URL keyword arguments.
        """

        url_kwargs = {}
        for key, attr_path in kwargs_config.items():
            url_kwargs[key] = (
                self.get_nested_attr(record, attr_path) if record else context.get(key)
            )
        return url_kwargs

    def get_nested_attr(self, obj, attr_path):
        """
        Retrieves a nested attribute from an object based on a specified attribute path. This
        function traverses the object's attributes using the provided path, returning the final
        attribute value or None if any part of the path is not found.

        Args:
            self: The instance of the class.
            obj: The object from which to retrieve the nested attribute.
            attr_path (str): A string representing the path to the nested attribute, using double
                underscores to separate levels.

        Returns:
            The value of the nested attribute, or None if any attribute in the path does not exist.
        """

        try:
            for attr in attr_path.split("__"):
                obj = getattr(obj, attr)
            return obj
        except AttributeError:
            return None

    def generate_default_urls(self):
        """
        Generates default URL configurations for standard actions using the model's slug or pk.
        """
        model = self.Meta.model
        slug_field = "slug" if hasattr(model, "slug") else "pk"
        namespace = getattr(
            self, "url_namespace", f"{model._meta.app_label}:{model._meta.model_name}"
        )

        return {
            "add": {
                "name": f"{namespace}:new",
                "kwargs": {},
            },
            "show": {
                "name": f"{namespace}:show",
                "kwargs": {slug_field: slug_field},
            },
            "edit": {
                "name": f"{namespace}:edit",
                "kwargs": {slug_field: slug_field},
            },
            "delete": {
                "name": f"{namespace}:delete",
                "kwargs": {slug_field: slug_field},
            },
        }


class ActionsColumnMixin(ActionUrlMixin, tables.Table):

    # Declare the column so the metaclass always knows about it
    actions = tables.Column(
        verbose_name="Actions",
        orderable=False,
        accessor="pk",
        empty_values=(),
    )

    available_actions = ["show", "edit", "delete"]  # Defaults
    action_icon_map = {
        "show": "eye",
        "edit": "edit",
        "delete": "trash-alt",
        "promote": "level-up-alt",
        "manage": "list-check",
    }
    action_title_map = {
        "add": "Add",
        "show": "View",
        "edit": "Edit",
        "delete": "Delete",
        "promote": "Promote",
        "manage": "Manage",
    }

    def get_icon_for_action(self, action):
        return self.action_icon_map.get(action, "question-circle")

    def get_title_for_action(self, action):
        return self.action_title_map.get(action, action.capitalize())

    def get_actions(self, record, user=None, include_add=False):
        """
        Get a list of actions for a given record, including custom ones defined in the table.
        """
        actions = []
        for action in self.available_actions:
            url = self.get_url(action, record=record)
            if url:
                actions.append({
                    "url": url,
                    "icon": self.get_icon_for_action(action),
                    "title": self.get_title_for_action(action),
                })
        return actions

    def is_allowed_action(self, user, action, record):
        """
        Check if the user has permission to perform an action on a record.
        """
        if user:
            return user.has_perm(
                f"app.{action}_{record._meta.model_name}"
            ) or self.custom_permission_check(user, action)
        return True

    def custom_permission_check(self, user, action):
        if not user:
            return False
        leader_admin = is_leader_admin(user)
        faculty_admin = is_faculty_admin(user) or is_department_admin(user)
        return leader_admin or faculty_admin or (
            action == "promote" and user.user_type in ["LEADER", "FACULTY", "FACILITY_FACULTY"]
        )

    def render_actions(self, value, record):
        """
        Render the actions column with icons for each available action.
        """
        actions_html = [
            f'<a href="{action["url"]}" title="{action["title"]}">'
            f'<i class="fas fa-{action["icon"]}"></i></a>'
            for action in self.get_actions(record, user=self.user)
        ]
        return (
            mark_safe(" ".join(actions_html))
            if actions_html
            else mark_safe("<span>No Actions Available</span>")
        )

    def add_actions_column(self):
        """
        Dynamically add an 'actions' column to the table.
        """
        if "actions" in self.base_columns:
            return

        # Column already declared at class definition; keep for compatibility
        self.base_columns["actions"] = self.actions

    def __init__(self, *args, user=None, **kwargs):
        # Copy base_columns per-instance so we don't mutate the class definition
        self.base_columns = self.base_columns.copy()
        if getattr(self, "available_actions", None):
            self.add_actions_column()
            # Ensure actions isn't filtered out when Meta.fields is set
            if getattr(self, "_meta", None) and getattr(self._meta, "fields", None):
                if "actions" not in self._meta.fields:
                    self._meta.fields = tuple(self._meta.fields) + ("actions",)
        else:
            # If no actions configured, drop the column entirely
            self.base_columns.pop("actions", None)

        super().__init__(*args, **kwargs)
        self.user = user  # Store the user for permission checks in render

        if user and (user.is_admin or is_leader_admin(user) or is_faculty_admin(user)):
            self.add_admin_columns()

    def add_admin_columns(self):
        self.base_columns["admin"] = tables.Column(verbose_name="Admin Actions")


class OrganizationLabelMixin:
    """
    Mixin to dynamically update table `verbose_name` and column labels based on
    the user's organization's `OrganizationLabel` model.
    """

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self.organization = (
            self.get_user_organization(user) if user and user.is_authenticated else None
        )
        super().__init__(*args, **kwargs)
        if self.organization:
            self.update_table_and_column_labels()

    def get_user_organization(self, user):
        try:
            return user.get_profile().get_root_organization()
        except ObjectDoesNotExist:
            return None

    def update_table_and_column_labels(self):
        if not self.organization:
            return

        try:
            org_labels = self.organization.labels
        except ObjectDoesNotExist:
            org_labels = None

        if org_labels:
            model_name = self.Meta.model._meta.model_name
            self.Meta.verbose_name = self.get_dynamic_verbose_name(
                model_name, org_labels
            )

            for column_name, column in self.base_columns.items():
                new_verbose_name = self.get_dynamic_verbose_name(
                    column_name, org_labels
                )
                if new_verbose_name:
                    column.verbose_name = new_verbose_name

    def get_dynamic_verbose_name(self, field_name, org_labels):
        field_label_name = f"{field_name}_label"
        return getattr(
            org_labels, field_label_name, camel_case_to_spaces(field_name).title()
        )
