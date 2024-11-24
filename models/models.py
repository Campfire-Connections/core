# core/models/models.py

from django.contrib.auth import get_user_model
from django.db import models
from typing import Any
from ..fields import AutoCreatedField, AutoLastModifiedField, StatusField, MonitorField

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    
    created = AutoCreatedField('created')
    modified = AutoLastModifiedField('modified')

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Overriding the save method to update the modified field.
        """
    
    class Meta:
        abstract = True


class TimeFramedModel(models.Model):
    """
    An abstract base class model that provides ``start``
    and ``end`` fields to record a timeframe.
    """
    
    start = models.DateTimeField('start', null=True, blank=True)
    end = models.DateTimeField('end', null=True, blank=True)

    class Meta:
        abstract = True


class StatusModel(models.Model):
    """
    An abstract base class model with a ``status`` field that
    automatically uses a ``STATUS`` class attribute of choices, a
    ``status_changed`` date-time field that records when ``status``
    was last modified, and an automatically-added manager for each
    status that returns objects with that status only.
    """
    
    status = StatusField('status')
    status_changed = MonitorField('status changed', monitor='status')

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Overriding the save method to update the status_changed field.
        """
    
    class Meta:
        abstract = True


def add_status_query_managers(sender: type[models.Model], **kwargs: Any) -> None:
    """
    Add a Querymanager for each status item dynamically.
    """
    if not issubclass(sender, StatusModel):
        return

    default_manager = sender._meta.default_manager
    assert default_manager is not None

    for value, display in getattr(sender, 'STATUS', ()):
        if _field_exists(sender, value):
            raise ImproperlyConfigured(
                "StatusModel: Model '%s' has a field named '%s' which "
                "conflicts with a status of the same name."
                % (sender.__name__, value)
            )
        sender.add_to_class(value, QueryManager(status=value))

    sender._meta.default_manager_name = default_manager.name


def add_timeframed_query_manager(sender: type[models.Model], **kwargs: Any) -> None:
    """
    Add a QueryManager for a specific timeframe.
    """
    if not issubclass(sender, TimeFramedModel):
        return
    if _field_exists(sender, 'timeframed'):
        raise ImproperlyConfigured(
            "Model '%s' has a field named 'timeframed' "
            "which conflicts with the TimeFramedModel manager."
            % sender.__name__
        )
    sender.add_to_class('timeframed', QueryManager(
        (models.Q(start__lte=now) | models.Q(start__isnull=True))
        & (models.Q(end__gte=now) | models.Q(end__isnull=True))
    ))


models.signals.class_prepared.connect(add_status_query_managers)
models.signals.class_prepared.connect(add_timeframed_query_manager)


def _field_exists(model_class: type[models.Model], field_name: str) -> bool:
    """
    Check if a field exists in the model class.
    """
    return field_name in [f.attname for f in model_class._meta.local_fields]
