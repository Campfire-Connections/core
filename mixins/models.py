# core/mixins/models.py

import uuid
from PIL import Image
from io import BytesIO
from rest_framework import serializers
from datetime import datetime
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile


# Enhanced NameDescriptionMixin with validation and better UX
class NameDescriptionMixin(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Make name unique
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        """Optional custom validation."""
        if len(self.name) < 3:
            raise ValidationError(_("Name must be at least 3 characters long."))

    class Meta:
        abstract = True


# Enhanced TimestampMixin with optional datetime formatting
class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def formatted_creation_date(self):
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")

    class Meta:
        abstract = True


# SoftDeleteMixin with a restore method and query manager for soft-deleted records
class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = now()
        self.save()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    @classmethod
    def get_active_objects(cls):
        """Return only active objects (not soft-deleted)."""
        return cls.objects.filter(is_deleted=False)

    @classmethod
    def get_deleted_objects(cls):
        """Return only deleted objects."""
        return cls.objects.filter(is_deleted=True)

    class Meta:
        abstract = True


# Enhanced AuditMixin with last activity tracking
class AuditMixin(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_%(class)s_set",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="updated_%(class)s_set",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    last_activity_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="last_activity_%(class)s_set",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        """Automatically set last_activity_by to updated_by."""
        if self.updated_by:
            self.last_activity_by = self.updated_by
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class SlugMixin(models.Model):
    slug = models.SlugField(max_length=255, blank=True)

    context_field = None  # Define the parent context field

    def generate_slug(self, field=None, pattern=None):
        """
        Generates a slug. Optionally, you can provide a field or pattern.
        pattern: E.g., '{name}-{date}'
        """
        if pattern:
            return slugify(
                pattern.format(
                    name=getattr(self, "name", ""),
                    date=now().strftime("%Y-%m-%d"),
                    random=uuid.uuid4().hex[:6],  # Random string to ensure uniqueness
                )
            )

        if field and hasattr(self, field):
            return slugify(f"{getattr(self, field)}")
        elif hasattr(self, "name"):
            return slugify(f"{self.name}")
        elif hasattr(self, "title"):
            return slugify(f"{self.title}")
        else:
            return slugify(str(self))

    def is_slug_unique(self, slug):
        """
        Checks if a slug is unique within the specified context.
        """
        filters = {"slug": slug}
        if self.context_field and hasattr(self, self.context_field):
            filters[self.context_field] = getattr(self, self.context_field)
        return not self.__class__.objects.filter(**filters).exists()

    def save(self, *args, **kwargs):
        """
        Automatically generates a slug, ensuring uniqueness within the specified context.
        """
        if not self.slug:
            self.slug = self.generate_slug()
            original_slug = self.slug
            counter = 1

            while not self.is_slug_unique(self.slug):
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


# OrderedModelMixin with helper methods to move objects up/down in the order
class OrderedModelMixin(models.Model):
    order = models.PositiveIntegerField(default=0)

    def move_up(self):
        """Move the object one position up."""
        if self.order > 0:
            self.order -= 1
            self.save()

    def move_down(self):
        """Move the object one position down."""
        self.order += 1
        self.save()

    class Meta:
        abstract = True
        ordering = ["order"]


# ActiveMixin with helper methods to activate/deactivate objects
class ActiveMixin(models.Model):
    is_active = models.BooleanField(default=True)

    def activate(self):
        self.is_active = True
        self.save()

    def deactivate(self):
        self.is_active = False
        self.save()

    class Meta:
        abstract = True


# UUIDMixin for universally unique ID support with better UUID handling
class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def regenerate_uuid(self):
        """Generate a new UUID for the instance."""
        self.id = uuid.uuid4()
        self.save()

    class Meta:
        abstract = True


# TrackChangesMixin with detailed change logs
class TrackChangesMixin(models.Model):
    change_message = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            self.change_message = "Updated: {}".format(", ".join(self.changed_fields))
        else:
            self.change_message = "Created"
        super().save(*args, **kwargs)

    @property
    def changed_fields(self):
        if not self.pk:
            return []
        old_values = self.__class__.objects.get(pk=self.pk)
        changed_fields = []
        for field in self._meta.get_fields():
            if not hasattr(field, "attname"):
                continue
            old_value = getattr(old_values, field.attname, None)
            new_value = getattr(self, field.attname, None)
            if old_value != new_value:
                changed_fields.append(field.name)
        return changed_fields

    class Meta:
        abstract = True


# GenericRelationMixin with additional utility methods
class GenericRelationMixin(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def get_related_model(self):
        """Returns the model class for the related object."""
        return self.content_type.model_class()

    def get_related_instance(self):
        """Returns the instance of the related object."""
        return self.content_type.get_object_for_this_type(id=self.object_id)

    class Meta:
        abstract = True


# ImageMixin with auto-resize and thumbnail generation
class ImageMixin(models.Model):
    image = models.ImageField(upload_to="images/", null=True, blank=True)

    def resize_image(self, width, height):
        """Resize the image to the given dimensions."""
        if self.image:
            img = Image.open(self.image)
            img = img.resize((width, height), Image.ANTIALIAS)
            output = BytesIO()
            img.save(output, format="JPEG")
            output.seek(0)
            self.image = SimpleUploadedFile(
                self.image.name, output.read(), content_type="image/jpeg"
            )
            self.save()

    class Meta:
        abstract = True


# SEOFieldsMixin enhanced for default SEO values and validation
class SEOFieldsMixin(models.Model):
    seo_title = models.CharField(max_length=70, blank=True, null=True)
    seo_description = models.CharField(max_length=160, blank=True, null=True)
    seo_keywords = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        if not self.seo_title:
            self.seo_title = getattr(self, "name", None) or getattr(
                self, "title", "Untitled"
            )
        if not self.seo_description:
            self.seo_description = f"Learn more about {self.seo_title}."
        if len(self.seo_description) > 160:
            raise ValidationError(_("SEO description must be under 160 characters."))

    class Meta:
        abstract = True


# ParentChildMixin with recursive retrieval and depth limit
class ParentChildMixin(models.Model):
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    def get_all_children(self, max_depth=5, current_depth=0):
        """Recursively get all children of the current object, up to a max depth."""
        if current_depth >= max_depth:
            return []
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(
                child.get_all_children(
                    max_depth=max_depth, current_depth=current_depth + 1
                )
            )
        return children

    class Meta:
        abstract = True


# DateRangeMixin with support for validation and enhanced date handling
class DateRangeMixin(models.Model):
    start = models.DateTimeField(_("start"), default=now)
    end = models.DateTimeField(_("end"))

    def clean(self):
        if self.end <= self.start:
            raise ValidationError(_("End date must be after start date"))
        super().clean()

    def duration(self):
        """Returns the duration between start and end."""
        return self.end - self.start

    class Meta:
        abstract = True


# Enhanced serializers for more flexible create/update operations
class CreateUpdateSerializerMixin(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

        if fields:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class HierarchicalEntity(
    NameDescriptionMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    SlugMixin,
    ActiveMixin,
    ImageMixin,
    ParentChildMixin,
):
    """
    Abstract base for tree-structured domain objects (Organization/Facility/Faction).
    Consolidates common behaviors (naming, slug, active, image, parent/child, audit/timestamps).
    """

    class Meta:
        abstract = True
