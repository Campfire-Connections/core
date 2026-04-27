from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import camel_case_to_spaces

from core.tables.actions import ActionUrlMixin, ActionsColumnMixin


class OrganizationLabelMixin:
    """
    Dynamically update table verbose names and column labels from organization labels.
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

        if not org_labels:
            return

        model_name = self.Meta.model._meta.model_name
        self.Meta.verbose_name = self.get_dynamic_verbose_name(
            model_name, org_labels
        )

        for column_name, column in self.base_columns.items():
            new_verbose_name = self.get_dynamic_verbose_name(column_name, org_labels)
            if new_verbose_name:
                column.verbose_name = new_verbose_name

    def get_dynamic_verbose_name(self, field_name, org_labels):
        field_label_name = f"{field_name}_label"
        return getattr(
            org_labels, field_label_name, camel_case_to_spaces(field_name).title()
        )
