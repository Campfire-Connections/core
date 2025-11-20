from datetime import date

from django.test import TestCase

from organization.models import Organization
from facility.models import Facility
from faction.models import Faction
from course.models.course import Course
from course.models.requirement import Requirement
from enrollment.models.organization import OrganizationEnrollment, OrganizationCourse
from enrollment.models.facility import FacilityEnrollment
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
