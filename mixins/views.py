# core/mixins/views.py

from django.contrib.auth.mixins import (
    PermissionRequiredMixin as BasePermissionRequiredMixin,
    UserPassesTestMixin,
    LoginRequiredMixin as BaseLoginRequiredMixin,
)
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class LoginRequiredMixin(BaseLoginRequiredMixin):
    login_url = "/login/"
    redirect_field_name = "next"

    def handle_no_permission(self):
        messages.info(self.request, "Please log in to access this page.")
        self.request.session["original_url"] = self.request.get_full_path()
        return super().handle_no_permission()


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.warning(
            self.request, "You do not have permission to access this page."
        )
        return redirect("forbidden")


class SuperUserRequired(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "This page is restricted to superusers.")
        return redirect("forbidden")


class FormMessagesMixin:
    success_message = ""
    error_message = ""
    success_message_level = messages.SUCCESS
    error_message_level = messages.ERROR

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            dynamic_message = self.success_message.format(obj=form.instance)
            messages.add_message(
                self.request, self.success_message_level, dynamic_message
            )
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.error_message:
            dynamic_message = self.error_message.format(obj=form.instance)
            messages.add_message(
                self.request, self.error_message_level, dynamic_message
            )
        return response


class DynamicRedirectMixin:
    """
    Mixin class that provides dynamic URL redirection based on the presence of a custom method.
    This mixin overrides the default success URL retrieval to allow for a dynamic success URL if
    the method `get_dynamic_success_url` is defined in the subclass.

    Methods:
        get_success_url(): Returns a dynamic success URL if available; otherwise, it falls back to
            the default implementation.
    """

    def get_success_url(self):
        """
        Retrieves the success URL to redirect to after a successful operation. This method can be
        overridden in subclasses to provide a custom success URL based on specific conditions or
        logic.

        Args:
            self: The instance of the class.

        Returns:
            str: The URL to redirect to upon success.
        """

        if hasattr(self, "get_dynamic_success_url"):
            return self.get_dynamic_success_url()
        return super().get_success_url()


class AjaxFormMixin:
    """
    Mixin class that provides AJAX support for form handling in views. This mixin overrides the
    default form validation methods to return JSON responses for AJAX requests, allowing for
    seamless integration with client-side JavaScript.

    Methods:
        form_valid(form): Handles valid form submissions and returns a JSON response with a success
            message and redirect URL for AJAX requests.
        form_invalid(form): Handles invalid form submissions and returns a JSON response with error
            details for AJAX requests.

    Args:
        self: The instance of the class.
        form: The form that has been submitted.
    """

    def form_valid(self, form):
        """
        Handles valid form submissions and returns a response based on the request type. If the
        request is an AJAX request, it returns a JSON response indicating success along with a
        redirect URL; otherwise, it delegates to the default form handling behavior.

        Args:
            self: The instance of the class.
            form: The valid form that has been submitted.

        Returns:
            JsonResponse: A JSON response indicating success and the redirect URL for AJAX
                requests, or the default response for non-AJAX requests.
        """

        if self.request.is_ajax():
            return JsonResponse(
                {"success": True, "redirect_url": self.get_success_url()}
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handles invalid form submissions and returns an appropriate response based on the request
        type. If the request is an AJAX request, it returns a JSON response containing the
        validation errors; otherwise, it falls back to the default behavior for invalid forms.

        Args:
            self: The instance of the class.
            form: The invalid form that has been submitted.

        Returns:
            JsonResponse: A JSON response indicating failure and containing the form errors for
                AJAX requests, or the default response for non-AJAX requests.
        """

        if self.request.is_ajax():
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


class PermissionRequiredMixin:
    """
    Mixin class that enforces permission requirements for views. This mixin checks if the user has
    the specified permission before allowing access to the view, raising a PermissionDenied
    exception if the user lacks the necessary permission.

    Attributes:
        permission_required (str): The permission required to access the view.

    Methods:
        dispatch(request, *args, **kwargs): Checks user permissions before dispatching the request
        to the view.

    Args:
        self: The instance of the class.
        request: The HTTP request object.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.
    """

    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        """
        Handles the dispatching of requests to the view while enforcing permission requirements.
        This method checks if the user has the necessary permission to access the view and raises a
        PermissionDenied exception if the permission is not granted.

        Args:
            self: The instance of the class.
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Raises:
            PermissionDenied: If the user does not have the required permission to access the view.
        """

        if self.permission_required and not request.user.has_perm(
            self.permission_required
        ):
            raise PermissionDenied(
                _("You do not have permission to perform this action.")
            )
        return super().dispatch(request, *args, **kwargs)


class ObjectPermissionRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        obj = self.get_object()
        if isinstance(self.permission_required, (list, tuple)):
            return all(
                self.request.user.has_perm(perm, obj)
                for perm in self.permission_required
            )
        return self.request.user.has_perm(self.permission_required, obj)

    def handle_no_permission(self):
        messages.error(
            self.request, "You do not have permission to perform this action."
        )
        return redirect("forbidden")


class UserGroupRequiredMixin(UserPassesTestMixin):
    required_groups = []

    def test_func(self):
        return any(
            group.name in self.required_groups
            for group in self.request.user.groups.all()
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            "You do not have the required group membership to access this page.",
        )
        return redirect("forbidden")


class CustomRedirectMixin:
    success_redirect_url = None
    failure_redirect_url = None

    def get_success_redirect_url(self):
        return self.success_redirect_url or self.request.GET.get("next", "/")

    def get_failure_redirect_url(self):
        return self.failure_redirect_url or "/forbidden/"

    def redirect_on_condition(self, condition, success=True):
        if condition:
            return redirect(self.get_success_redirect_url())
        return redirect(self.get_failure_redirect_url())


class DynamicLoginRedirectMixin(LoginRequiredMixin):
    def get_redirect_url(self):
        if self.request.user.is_staff:
            return "/staff/dashboard/"
        elif self.request.user.is_superuser:
            return "/admin/dashboard/"
        return super().get_redirect_url()


class BaseViewMixin:
    """
    A base mixin for all views, providing utilities for dynamic success URLs.
    """

    success_url_pattern = None  # Define in child views if needed
    success_url_params = None  # Dictionary of kwargs to reverse URL

    def get_success_url(self):
        """
        Dynamically generate the success URL using `success_url_pattern` and `success_url_params`.
        """
        if not self.success_url_pattern:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing a `success_url_pattern`. "
                "Define `success_url_pattern` or override `get_success_url`."
            )

        params = self.get_success_url_params()
        try:
            return reverse(self.success_url_pattern, kwargs=params)
        except NoReverseMatch as e:
            raise ImproperlyConfigured(
                f"Failed to reverse URL for pattern '{self.success_url_pattern}' with params {params}: {e}"
            )

    def get_success_url_params(self):
        """
        Return the parameters required for reversing `success_url_pattern`.
        Override in child classes if needed.
        """
        if self.success_url_params:
            return self.success_url_params

        # Default to the model's slug or pk
        if hasattr(self.object, "slug"):
            return {"slug": self.object.slug}
        elif hasattr(self.object, "pk"):
            return {"pk": self.object.pk}
        else:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} cannot determine success URL parameters. "
                "Define `success_url_params` or override `get_success_url_params`."
            )


class ActionContextMixin:
    action = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.action:
            context["action"] = self.action
        return context
