import json
from datetime import date
from types import SimpleNamespace
from contextlib import contextmanager

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from organization.models import Organization
from facility.models import Facility
from faction.models import Faction
from faction.models.leader import LeaderProfile
from course.models.course import Course
from course.models.requirement import Requirement
from enrollment.models.organization import OrganizationEnrollment, OrganizationCourse
from enrollment.models.facility import FacilityEnrollment
from enrollment.models.enrollment import ActiveEnrollment
from core.context_processors import (
    active_enrollment as active_enrollment_context,
    user_profile as user_profile_context,
)
from core.views.base import BaseDashboardView
from core.widgets import TextWidget
from core.models.dashboard import DashboardLayout
from core.models.navigation import NavigationPreference
from core.menu_registry import build_menu_for_user
from user.models import (
    create_profile as create_profile_signal,
    save_profile as save_profile_signal,
    update_profile_slug as update_profile_slug_signal,
)
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

    def _create_superuser(self, **overrides):
        """
        Helper for view tests that need an authenticated admin.
        """
        params = {
            "username": overrides.pop("username", "test.superuser"),
            "email": overrides.pop("email", "admin@example.com"),
            "password": overrides.pop("password", "pass12345"),
        }
        params.update(overrides)
        return User.objects.create_superuser(**params)


@contextmanager
def mute_profile_signals():
    receivers = [
        create_profile_signal,
        save_profile_signal,
        update_profile_slug_signal,
    ]
    for receiver in receivers:
        post_save.disconnect(receiver, sender=User)
    try:
        yield
    finally:
        for receiver in receivers:
            post_save.connect(receiver, sender=User)


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


class ActiveEnrollmentContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        with mute_profile_signals():
            self.user = User.objects.create_user(
                username="active.user",
                password="pass12345",
                user_type=User.UserType.LEADER,
            )

    def _build_request(self):
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        return request

    def test_returns_placeholder_when_record_missing(self):
        request = self._build_request()
        context = active_enrollment_context(request)
        enrollment = context["active_enrollment"]
        self.assertIsInstance(enrollment, ActiveEnrollment)
        self.assertEqual(enrollment.user_id, self.user.id)

    def test_uses_existing_session_record(self):
        record = ActiveEnrollment.objects.create(user_id=self.user.id)
        request = self._build_request()
        request.session["active_enrollment_id"] = record.id
        context = active_enrollment_context(request)
        self.assertEqual(context["active_enrollment"].id, record.id)


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

    def test_layout_order_is_respected(self):
        DashboardLayout.objects.create(
            user=self.user,
            portal_key="test-dashboard",
            layout=json.dumps(["hidden", "visible"]),
        )
        view = self._build_view()
        widgets = view.build_widgets()
        self.assertEqual([w["key"] for w in widgets][:2], ["hidden", "visible"])


class MenuRegistryTests(BaseDomainTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        with mute_profile_signals():
            cls.leader = User.objects.create_user(
                username="leader.menu",
                password="pass12345",
                user_type=User.UserType.LEADER,
            )
            cls.leader_without_faction = User.objects.create_user(
                username="leader.no.faction",
                password="pass12345",
                user_type=User.UserType.LEADER,
            )
        LeaderProfile.objects.create(
            user=cls.leader,
            organization=cls.organization,
            faction=cls.faction,
        )

    def _find_menu_item(self, menu, label):
        for section in menu:
            if section["label"] == label:
                return section
        return None

    def test_leader_menu_has_manage_enrollments_link(self):
        menu_data = build_menu_for_user(self.leader)
        section = self._find_menu_item(menu_data["primary"], "Faction Mgmt")
        self.assertIsNotNone(section)
        enrollment_entry = next(
            (child for child in section["children"] if child["label"] == "Manage Enrollments"),
            None,
        )
        self.assertIsNotNone(enrollment_entry)
        self.assertIn(self.faction.slug, enrollment_entry["url"])

    def test_leader_without_faction_gets_disabled_link(self):
        menu_data = build_menu_for_user(self.leader_without_faction)
        section = self._find_menu_item(menu_data["primary"], "Faction Mgmt")
        enrollment_entry = next(
            (child for child in section["children"] if child["label"] == "Manage Enrollments"),
            None,
        )
        self.assertIsNotNone(enrollment_entry)
        self.assertIsNone(enrollment_entry["url"])

    def test_quick_menu_contains_shortcut(self):
        menu_data = build_menu_for_user(self.leader)
        self.assertTrue(
            any(item["label"] == "Faction Dashboard" for item in menu_data["quick"])
        )

    def test_favorite_entries_are_added_to_quick_menu(self):
        menu_data = build_menu_for_user(
            self.leader, favorites=["leader_enrollments"]
        )
        favorite_entry = next(
            (item for item in menu_data["quick"] if item.get("key") == "leader_enrollments"),
            None,
        )
        self.assertIsNotNone(favorite_entry)
        self.assertTrue(favorite_entry.get("favorite"))


class NavigationPreferenceModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pref.user",
            password="pass12345",
            user_type=User.UserType.ADMIN,
        )

    def test_add_and_remove_favorites(self):
        preferences = NavigationPreference.objects.create(user=self.user)
        preferences.add_favorite("dashboard")
        self.assertIn("dashboard", preferences.favorite_keys)
        preferences.remove_favorite("dashboard")
        self.assertNotIn("dashboard", preferences.favorite_keys)
