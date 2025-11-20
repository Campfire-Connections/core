import json
from uuid import uuid4

from django.utils.text import slugify


class DashboardWidget:
    """
    Base widget helper that normalizes how dashboard cards are rendered across portals.

    Sub-classes should override `widget_type` and `get_payload` to inject the data
    their card needs (tables, charts, actions, etc).
    """

    widget_type = "text"
    default_width = 6  # Bootstrap grid columns
    default_priority = 10
    template_name = None

    def __init__(
        self,
        request,
        title,
        width=None,
        priority=None,
        slug=None,
        template_name=None,
        key=None,
        **kwargs,
    ):
        self.request = request
        self.title = title
        self.width = width or self.default_width
        self.priority = priority if priority is not None else self.default_priority
        base_slug = slug or slugify(title) or self.__class__.__name__.lower()
        # Slug is only used for DOM ids, so a short random suffix keeps it unique.
        self.slug = f"{base_slug}-{uuid4().hex[:5]}"
        self.key = key or base_slug
        self.extra = kwargs
        if template_name:
            self.template_name = template_name

    def get_payload(self):
        """Return the widget-specific payload."""
        return {}

    def as_dict(self):
        payload = self.get_payload() or {}
        payload.update(
            {
                "slug": self.slug,
                "title": self.title,
                "width": self.width,
                "priority": self.priority,
                "type": self.widget_type,
                "template": self.template_name,
                "key": self.key or self.slug,
            }
        )
        return payload


class TextWidget(DashboardWidget):
    widget_type = "text"
    template_name = "widgets/text.html"

    def get_payload(self):
        return {"content": self.extra.get("content", "")}


class ActionsWidget(DashboardWidget):
    widget_type = "actions"
    template_name = "widgets/actions.html"

    def get_payload(self):
        return {"actions": self.extra.get("actions", [])}


class MetricsWidget(DashboardWidget):
    widget_type = "metrics"
    template_name = "widgets/metrics.html"

    def get_payload(self):
        metrics = self.extra.get("metrics", [])
        normalized = [
            {
                "label": metric.get("label"),
                "value": metric.get("value"),
                "delta": metric.get("delta"),
                "description": metric.get("description"),
            }
            for metric in metrics
        ]
        return {"metrics": normalized}


class TableWidget(DashboardWidget):
    widget_type = "table"

    def get_payload(self):
        table_class = self.extra.get("table_class")
        queryset = self.extra.get("queryset")
        if not table_class or queryset is None:
            return {"table": None}

        table = table_class(queryset, request=self.request)
        return {"table": table}


class ChartWidget(DashboardWidget):
    widget_type = "chart"

    def get_payload(self):
        chart_config = self.extra.get("chart_config", {})
        return {
            "chart_id": f"chart-{self.slug}",
            "chart_config": json.dumps(chart_config),
        }


class ListWidget(DashboardWidget):
    """
    Simple list widget suited for announcements, resources, or action feeds.
    Each item should be a dict with optional `title`, `subtitle`, `url`, or `meta`.
    """

    widget_type = "list"
    template_name = "widgets/list.html"

    def get_payload(self):
        items = self.extra.get("items", [])
        normalized = [
            {
                "title": item.get("title"),
                "subtitle": item.get("subtitle"),
                "url": item.get("url"),
                "meta": item.get("meta"),
                "icon": item.get("icon"),
            }
            for item in items
        ]
        empty_message = self.extra.get(
            "empty_message", "There is nothing to show here right now."
        )
        return {"items": normalized, "empty_message": empty_message}


class AnnouncementWidget(ListWidget):
    template_name = "widgets/announcements.html"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("empty_message", "No announcements yet.")
        super().__init__(*args, **kwargs)


class ResourceListWidget(ListWidget):
    template_name = "widgets/resources.html"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("empty_message", "No resources available.")
        super().__init__(*args, **kwargs)
