# core/mixins/forms.py

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import HttpResponseRedirect

class FormValidMixin:
    """
    Automatically adds the request user's info (created_by and updated_by) to the form instance when valid.
    """
    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
            form.instance.updated_by = self.request.user
        return super().form_valid(form)

# Enhancements and new form-related mixins start here

class SuccessMessageMixin:
    """
    Adds a success message to the user when the form is submitted successfully.
    """
    success_message = ''

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class ErrorMessageMixin:
    """
    Adds an error message when form validation fails.
    """
    error_message = ''

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.error_message:
            messages.error(self.request, self.error_message)
        return response


class FormAutoSaveMixin:
    """
    Automatically saves a form's progress periodically via AJAX or at certain intervals.
    Useful for long forms.
    """
    def auto_save_form(self, form):
        # Implement logic to save form data in session or cache
        self.request.session['form_data'] = form.cleaned_data

    def form_valid(self, form):
        self.auto_save_form(form)
        return super().form_valid(form)


class PreventDoubleSubmitMixin:
    """
    Prevents double form submissions by marking the form as submitted.
    """
    def form_valid(self, form):
        if self.request.session.get('form_submitted', False):
            messages.warning(self.request, "You have already submitted this form.")
            return HttpResponseRedirect(self.get_success_url())

        # Mark form as submitted
        self.request.session['form_submitted'] = True
        return super().form_valid(form)


class DynamicFormFieldsMixin:
    """
    Dynamically add or remove form fields based on request data or user permissions.
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
        # Example: Only add this field if the user is staff
        if self.request.user.is_staff:
            form.fields['staff_only_field'].required = True
            form.fields['staff_only_field'].widget.attrs['class'] = 'special-field'
        else:
            form.fields.pop('staff_only_field', None)


class FormTimestampMixin:
    """
    Adds a timestamp when the form is created or updated. This can be useful for logging and debugging purposes.
    """
    def form_valid(self, form):
        form.instance.timestamp = timezone.now()
        return super().form_valid(form)


class RedirectOnInvalidMixin:
    """
    Redirects to another URL if the form is invalid, instead of rendering the form again.
    This is useful if you want to avoid re-rendering the invalid form.
    """
    invalid_redirect_url = None

    def form_invalid(self, form):
        if self.invalid_redirect_url:
            messages.error(self.request, "Form submission failed. Please try again.")
            return HttpResponseRedirect(self.invalid_redirect_url)
        return super().form_invalid(form)


class ValidationErrorMixin:
    """
    Adds custom validation to forms by injecting additional validation logic.
    """
    def clean(self):
        cleaned_data = super().clean()
        # Example custom validation
        if 'end_date' in cleaned_data and 'start_date' in cleaned_data:
            if cleaned_data['end_date'] < cleaned_data['start_date']:
                raise ValidationError("End date cannot be before the start date.")
        return cleaned_data


class AjaxFormMixin:
    """
    Handle form submissions via AJAX to avoid full-page reloads.
    """
    def form_valid(self, form):
        if self.request.is_ajax():
            response_data = {
                "success": True,
                "redirect_url": self.get_success_url(),
                # Add other relevant data as needed
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


class ConditionalRedirectMixin:
    """
    Redirects based on a condition after the form is successfully submitted.
    Example: Redirect to different URLs based on user roles or form data.
    """
    def get_success_url(self):
        # Custom redirect logic based on user or form instance
        if self.request.user.is_staff:
            return '/staff/success/'
        return '/default/success/'


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
