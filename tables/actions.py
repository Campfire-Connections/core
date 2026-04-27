import logging

import django_tables2 as tables
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe

from core.utils import is_department_admin, is_faculty_admin, is_leader_admin

logger = logging.getLogger(__name__)


class ActionUrlMixin:
    """
    Resolve standard table action URLs such as add, show, edit, and delete.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_urls = self.generate_default_urls()

    def get_url(self, action, record=None, context=None):
        action_url_info = self.urls.get(action, {})
        url_name = action_url_info.get("name", f"{self.url_namespace}:{action}")
        kwargs_config = action_url_info.get("kwargs", {})
        url_kwargs = self.build_url_kwargs(kwargs_config, record, context)

        try:
            return reverse(url_name, kwargs=url_kwargs)
        except NoReverseMatch:
            if getattr(self, "debug_mode", False):
                logger.warning(
                    "URL reverse failed for action '%s' with kwargs %s",
                    action,
                    url_kwargs,
                )
            return "#"

    def build_url_kwargs(self, kwargs_config, record=None, context=None):
        context = context or {}
        url_kwargs = {}
        for key, attr_path in kwargs_config.items():
            url_kwargs[key] = (
                self.get_nested_attr(record, attr_path) if record else context.get(key)
            )
        return url_kwargs

    def get_nested_attr(self, obj, attr_path):
        try:
            for attr in attr_path.split("__"):
                obj = getattr(obj, attr)
            return obj
        except AttributeError:
            return None

    def generate_default_urls(self):
        model = self.Meta.model
        slug_field = "slug" if hasattr(model, "slug") else "pk"
        namespace = getattr(
            self, "url_namespace", f"{model._meta.app_label}:{model._meta.model_name}"
        )

        return {
            "add": {"name": f"{namespace}:new", "kwargs": {}},
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
    actions = tables.Column(
        verbose_name="Actions",
        orderable=False,
        accessor="pk",
        empty_values=(),
    )

    available_actions = ["show", "edit", "delete"]
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
        actions = []
        for action in self.available_actions:
            url = self.get_url(action, record=record)
            if url:
                actions.append(
                    {
                        "url": url,
                        "icon": self.get_icon_for_action(action),
                        "title": self.get_title_for_action(action),
                    }
                )
        return actions

    def is_allowed_action(self, user, action, record):
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
            action == "promote"
            and user.user_type in ["LEADER", "FACULTY", "FACILITY_FACULTY"]
        )

    def render_actions(self, value, record):
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
        if "actions" in self.base_columns:
            return
        self.base_columns["actions"] = self.actions

    def __init__(self, *args, user=None, **kwargs):
        self.base_columns = self.base_columns.copy()
        if getattr(self, "available_actions", None):
            self.add_actions_column()
            if getattr(self, "_meta", None) and getattr(self._meta, "fields", None):
                if "actions" not in self._meta.fields:
                    self._meta.fields = tuple(self._meta.fields) + ("actions",)
        else:
            self.base_columns.pop("actions", None)

        super().__init__(*args, **kwargs)
        self.user = user

        if user and (user.is_admin or is_leader_admin(user) or is_faculty_admin(user)):
            self.add_admin_columns()

    def add_admin_columns(self):
        self.base_columns["admin"] = tables.Column(verbose_name="Admin Actions")
