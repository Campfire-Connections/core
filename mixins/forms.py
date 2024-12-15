# core/mixins/forms.py

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect


class FormContextMixin:
    """
    Adds user context to forms and applies widget attributes dynamically.
    """

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.user = self.request.user
        form.apply_default_widget_attrs()
        return form


class FormValidationMixin:
    """
    Centralized validation logic to prevent redundancy.
    """

    def validate_date_range(self, cleaned_data, start_field, end_field):
        start_date = cleaned_data.get(start_field)
        end_date = cleaned_data.get(end_field)
        if start_date and end_date and start_date > end_date:
            raise ValidationError(f"{start_field} cannot be greater than {end_field}.")

    def clean(self):
        cleaned_data = super().clean()
        self.validate_date_range(cleaned_data, "start_date", "end_date")
        return cleaned_data


class SuccessMessageMixin:
    """
    Adds success messages for form submissions.
    """

    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class ErrorMessageMixin:
    """
    Adds error messages for invalid forms.
    """

    error_message = ""

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.error_message:
            messages.error(self.request, self.error_message)
        return response


class AjaxFormMixin:
    """
    Handle AJAX submissions for forms.
    """

    def form_valid(self, form):
        if self.request.is_ajax():
            response_data = {
                "success": True,
                "redirect_url": self.get_success_url(),
            }
            return JsonResponse(response_data)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.is_ajax():
            response_data = {
                "success": False,
                "errors": form.errors,
            }
            return JsonResponse(response_data, status=400)
        return super().form_invalid(form)


class PreventDoubleSubmitMixin:
    """
    Prevent duplicate submissions of a form.
    """

    def form_valid(self, form):
        if self.request.session.get("form_submitted", False):
            messages.warning(self.request, "You have already submitted this form.")
            return HttpResponseRedirect(self.get_success_url())

        # Mark form as submitted
        self.request.session["form_submitted"] = True
        return super().form_valid(form)


class DynamicFieldMixin:
    """
    Dynamically modify form fields based on user roles or request context.
    """

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        self.modify_form_fields(form)
        return form

    def modify_form_fields(self, form):
        """
        Modify form fields dynamically based on the user or request.
        This method can be customized per view.
        """
        if self.request.user.is_staff:
            form.fields['staff_only_field'].required = True
            form.fields['staff_only_field'].widget.attrs['class'] = 'special-field'
        else:
            form.fields.pop('staff_only_field', None)


class PrefillFormMixin:
    """
    Pre-fills form fields based on request data or existing instance data (e.g., user profile).
    """
    def get_initial(self):
        initial = super().get_initial()
        # Example: Prefill the email field with the current user's email
        if self.request.user.is_authenticated:
            initial['email'] = self.request.user.email
        return initial


class MultipleFormsMixin:
    """
    Handle multiple forms in a single view.
    """
    form_classes = {}

    def get_forms(self, *args, **kwargs):
        """
        Return instances of the forms defined in form_classes.
        """
        forms = {}
        for form_name, form_class in self.form_classes.items():
            forms[form_name] = form_class(*args, **kwargs)
        return forms

    def process_forms(self, request, *args, **kwargs):
        """
        Validate and process multiple forms.
        """
        forms = self.get_forms(*args, **kwargs)
        all_valid = all(form.is_valid() for form in forms.values())
        if all_valid:
            for form in forms.values():
                self.form_valid(form)
            return self.form_valid(forms)
        else:
            return self.form_invalid(forms)

    def form_valid(self, forms):
        # Process forms after validation
        for form in forms.values():
            form.save()
        return super().form_valid(forms)

    def form_invalid(self, forms):
        # Handle invalid forms
        return self.render_to_response(self.get_context_data(forms=forms))