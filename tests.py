from datetime import date
from types import SimpleNamespace

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model

from organization.models import Organization
from facility.models import Facility
from faction.models import Faction
from course.models.course import Course
from course.models.requirement import Requirement
from enrollment.models.organization import OrganizationEnrollment, OrganizationCourse
from enrollment.models.facility import FacilityEnrollment
from core.context_processors import user_profile as user_profile_context
from core.views.base import BaseDashboardView
from core.widgets import TextWidget
from core.models.dashboard import DashboardLayout
User = get_user_model()


class BaseDomainTestCase(TestCase):
    """
    Shared data builder that provisions a minimal but representative set of
    domain objects spanning multiple apps so individual modules can write
    focused tests without repeating boilerplate setup.
    """

    @classmethod
    def setUpTestData(cls):
        cls.parent_org = Organization.objects.create(
            name="Campfire Council",
            abbreviation="CC",
            max_depth=5,
        )
        cls.organization = Organization.objects.create(
            name="Cascade District",
            abbreviation="CD",
            parent=cls.parent_org,
            max_depth=5,
        )
        cls.facility = Facility.objects.create(
            name="River Bend Training Center",
            organization=cls.organization,
        )
        cls.faction = Faction.objects.create(
            name="Eagle Patrol",
            organization=cls.organization,
        )
        cls.requirement = Requirement.objects.create(name="Medical Release")
        cls.course = Course.objects.create(name="Navigation Basics")
        cls.course.requirements.add(cls.requirement)

        cls.org_enrollment = OrganizationEnrollment.objects.create(
            name="Summer 2025",
            organization=cls.organization,
            start=date(2025, 6, 1),
            end=date(2025, 6, 30),
        )
        cls.org_course = OrganizationCourse.objects.create(
            name="Navigation Basics Summer Cohort",
            course=cls.course,
            organization_enrollment=cls.org_enrollment,
        )
        cls.facility_enrollment = FacilityEnrollment.objects.create(
            name="River Bend Session 1",
            organization_enrollment=cls.org_enrollment,
            facility=cls.facility,
            start=date(2025, 6, 1),
            end=date(2025, 6, 15),
        )


class SlugAndHierarchyTests(BaseDomainTestCase):
    def test_slug_is_generated_for_new_entities(self):
        org = Organization.objects.create(
            name="Frontier District", abbreviation="FD", max_depth=5
        )
        self.assertEqual(org.slug, "frontier-district")

    def test_parent_descendant_collection_includes_children(self):
        ids = self.parent_org.get_descendant_ids()
        self.assertIn(self.organization.id, ids)


class UserProfileContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="noprof.user",
            password="pass12345",
            user_type=User.UserType.ADMIN,
        )

    def test_returns_placeholder_when_no_profile(self):
        request = self.factory.get("/")
        request.user = self.user

        context = user_profile_context(request)
        profile = context["user_profile"]

        self.assertEqual(profile.slug, "")
        self.assertTrue(hasattr(profile, "organization"))


class DummyDashboardView(BaseDashboardView):
    template_name = "leader/dashboard.html"
    portal_key = "test-dashboard"

    def get_registry_definitions(self):
        return [
            {
                "key": "visible",
                "widget": TextWidget,
                "title": "Visible",
                "options": {"content": "hello"},
            },
            {
                "key": "hidden",
                "widget": TextWidget,
                "title": "Hidden",
                "options": {"content": "secret"},
            },
        ]


class DashboardRegistryTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="dashboard.user",
            password="pass1234",
            user_type=User.UserType.ADMIN,
        )

    def _build_view(self):
        view = DummyDashboardView()
        request = self.factory.get("/")
        request.user = self.user
        view.request = request
        view.args = []
        view.kwargs = {}
        return view

    def test_hidden_preferences_filter_widgets(self):
        DashboardLayout.objects.create(
            user=self.user, portal_key="test-dashboard", hidden_widgets=["hidden"]
        )
        view = self._build_view()
        widgets = view.build_widgets()
        keys = [widget["key"] for widget in widgets]
        self.assertIn("visible", keys)
        self.assertNotIn("hidden", keys)
