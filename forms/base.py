# core/forms/base.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class BaseForm(forms.ModelForm):
    """
    A base form class that extends ModelForm to include user context and custom validation.
    This form allows for additional logic based on the user and provides methods for applying 
    default widget attributes and validating field combinations.

    Methods:
        __init__(*args, **kwargs): Initializes the form and captures the user context if provided.
        apply_default_widget_attrs(): Applies default attributes to all form field widgets.
        clean(): Cleans the form data and allows for custom validation logic.
        validate_field_combinations(field1, field2): Validates that the value of one field is not 
            greater than another field.
        save(commit=True): Saves the form data to a model instance, optionally committing the 
            changes to the database.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and captures the user context if provided.
        This constructor allows for the inclusion of a user object, which can be used for 
        context-specific logic within the form.

        Args:
            *args: Positional arguments to be passed to the parent class initializer.
            **kwargs: Keyword arguments to be passed to the parent class initializer, including an
                optional 'user' key.

        Returns:
            None
        """

    def apply_default_widget_attrs(self):
        """
        Applies default attributes to all form field widgets.
        This method ensures that each field widget has a default CSS class and marks required 
        fields appropriately.

        Args:
            self: The form instance containing the fields.

        Returns:
            None
        """

        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            if field.required:
                field.widget.attrs.setdefault('required', 'required')

    def clean(self):
        """
        Cleans the form data and allows for custom validation logic.
        This method invokes the parent class's clean method and provides a place to implement 
        additional validation rules before returning the cleaned data.

        Args:
            self: The form instance being cleaned.

        Returns:
            dict: The cleaned data from the form.

        Raises:
            ValidationError: If any custom validation fails during the cleaning process.
        """

        cleaned_data = super().clean()
        if 'name' in cleaned_data and len(cleaned_data['name']) < 3:
            self.add_error('name', _("Name must be at least 3 characters long."))
        return cleaned_data

    def validate_field_combinations(self, field1, field2):
        """
        Validates that the value of one field is not greater than another field.
        This method checks the cleaned data for the specified fields and raises a validation error
        if the condition is violated.

        Args:
            field1 (str): The name of the first field to compare.
            field2 (str): The name of the second field to compare.

        Returns:
            None

        Raises:
            ValidationError: If the value of field1 is greater than the value of field2.
        """


        value1 = self.cleaned_data.get(field1)
        value2 = self.cleaned_data.get(field2)
        if value1 and value2 and value1 > value2:
            raise ValidationError(
                _(f"{field1} cannot be greater than {field2}."),
                code='invalid_combination'
            )

    def save(self, commit=True):
        """
        Saves the form data to a model instance, optionally committing the changes to the database.
        This method also sets the 'created_by' and 'updated_by' fields on the instance if a user is
        provided.

        Args:
            commit (bool): A flag indicating whether to save the instance to the database. Defaults 
                to True.

        Returns:
            instance: The saved model instance.

        Raises:
            ValueError: If the instance cannot be saved due to validation errors.
        """

        instance = super().save(commit=False)
        if self.user and hasattr(instance, 'created_by'):
            instance.created_by = self.user
            instance.updated_by = self.user
        if commit:
            instance.save()
        return instance


class BaseFormNonModel(forms.Form):
    """
    A base form class that is not tied to a specific model.
    This form allows for the inclusion of user context and applies default widget attributes for 
    consistent styling.

    Methods:
        __init__(*args, **kwargs): Initializes the form and captures the user context if provided.
        apply_default_widget_attrs(): Sets default attributes for all form field widgets.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and captures the user context if provided.
        This constructor allows for the inclusion of a user object, which can be used for 
        context-specific logic within the form.

        Args:
            *args: Positional arguments to be passed to the parent class initializer.
            **kwargs: Keyword arguments to be passed to the parent class initializer, including an
                optional 'user' key.

        Returns:
            None
        """

        self.user = kwargs.pop('user', None)  # Pass user context if needed
        super().__init__(*args, **kwargs)
        self.apply_default_widget_attrs()

    def apply_default_widget_attrs(self):
        """
        Sets default attributes for all form field widgets.
        This function ensures that each field widget has a default CSS class applied for consistent
        styling across the form.

        Args:
            self: The form instance containing the fields.

        Returns:
            None
        """

        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
