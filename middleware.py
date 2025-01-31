# core/middleware.py

import logging
import inflect

from django.utils.deprecation import MiddlewareMixin

from django.template.context import RequestContext
from organization.context_processors import organization_labels


from enrollment.models.enrollment import ActiveEnrollment

logger = logging.getLogger(__name__)
p = inflect.engine()


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.debug("Request: %s %s", request.method, request.get_full_path())

    def process_response(self, request, response):
        logger.debug("Response: %s", response.status_code)
        return response


class ActiveEnrollmentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if active_enrollment_id := request.session.get("active_enrollment_id"):
                request.active_enrollment = ActiveEnrollment.objects.get(
                    id=active_enrollment_id
                )
            else:
                request.active_enrollment = ActiveEnrollment.objects.get(
                    user_id=request.user.id
                )
        return self.get_response(request)


class BreadcrumbMiddleware(MiddlewareMixin):
    def process_template_response(self, request, response):
        if hasattr(response, "context_data") and isinstance(
            response.context_data, dict
        ):
            labels_context = organization_labels(request)
            breadcrumbs = self.generate_breadcrumbs(request, labels_context)
            response.context_data["breadcrumbs"] = breadcrumbs
        return response

    def singlize_word(self, word):
        return p.singular_noun(word) or word

    def pluralize_word(self, word):
        if not isinstance(word, str):
            raise ValueError("Input to pluralize_word must be a string.")
        try:
            plural_word = p.plural(word)
            return plural_word
        except Exception as e:
            print(f"Error in pluralize_word: {e}")
            return word

    def should_skip_pluralization(self, segment, path, organization_labels):
        """
        Determine if a segment should skip pluralization based on its context.
        """
        # Example logic: Skip pluralizing if the segment matches specific path keys
        # like facility or department names, or if there's no label for it.
        if (
            segment in path  # Facility or department in path
            or f"{self.singlize_word(segment)}_label" in organization_labels  # Exists as a specific label
        ):
            return True
        return False

    def generate_breadcrumbs(self, request, context_data):
        """
        Generate breadcrumbs for the current request path.

        If an `organization_label` exists for a segment, it will be used.
        """
        breadcrumbs = [{"name": "Home", "url": "/"}]
        path = request.path.strip("/").split("/")
        url = ""

        # Attempt to fetch organization labels from context
        organization_labels = context_data.get("organization_labels", {})

        for segment in path:
            url += f"/{segment}"

            # Use the organization label if it exists
            if self.should_skip_pluralization(segment, path, organization_labels):
                label_name = organization_labels.get(
                    f"{segment}_label", segment.capitalize()
                )
            else:
                label_name = self.pluralize_word(
                    organization_labels.get(f"{segment}_label", segment.capitalize())
                )

            breadcrumbs.append({"name": label_name, "url": url})

        return breadcrumbs
