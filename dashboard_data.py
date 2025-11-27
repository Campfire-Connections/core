from django.core.cache import cache
from django.db.models import Count

from faction.models import Faction
from facility.models import Facility
from enrollment.models.attendee_class import AttendeeClassEnrollment
from enrollment.models.faculty import FacultyEnrollment
from course.models.facility_class import FacilityClass
from core.cache import cached, cache_key as shared_cache_key, CACHE_TIMEOUT

def get_leader_metrics(faction: Faction):
    if not faction:
        return []
    key = shared_cache_key("leader_metrics", faction.pk)
    return cached(
        key,
        CACHE_TIMEOUT,
        lambda: [
            {"label": "Leaders", "value": faction.member_count(user_type="leader")},
            {"label": "Attendees", "value": faction.member_count(user_type="attendee")},
            {"label": "Sub-factions", "value": faction.children.count()},
        ],
    )


def get_leader_resource_links(faction: Faction | None):
    key = shared_cache_key("leader_resources", faction.pk if faction else "global")
    return cached(
        key,
        CACHE_TIMEOUT,
        lambda: [
            {
                "title": "Faction Roster",
                "subtitle": "Review attendee contact info.",
                "url": "/factions/",
            },
            {
                "title": "Weekly Schedule",
                "subtitle": "Confirm upcoming assignments.",
                "url": "/leaders/manage/",
            },
        ],
    )


def get_attendee_resources(faction: Faction | None):
    key = shared_cache_key("attendee_resources", faction.pk if faction else "global")
    return cached(
        key,
        CACHE_TIMEOUT,
        lambda: [
            {
                "title": "Packing Checklist",
                "subtitle": "Make sure you bring everything you need.",
                "url": "#",
            },
            {
                "title": "Camp Code of Conduct",
                "subtitle": "Review expectations before arrival.",
                "url": "#",
            },
        ],
    )


def get_attendee_announcements(faction: Faction | None):
    key = shared_cache_key("attendee_announcements", faction.pk if faction else "global")
    return cached(
        key,
        CACHE_TIMEOUT,
        lambda: [
            {
                "title": f"Welcome to {faction.name if faction else 'camp'}",
                "subtitle": "Orientation starts Monday at 9am.",
                "meta": "",
            },
            {
                "title": "Don't forget lights-out",
                "subtitle": "Quiet hours begin at 10pm.",
                "meta": "",
            },
        ],
    )


def get_faculty_resources(facility: Facility | None):
    key = shared_cache_key("faculty_resources", facility.pk if facility else "global")
    return cached(
        key,
        CACHE_TIMEOUT,
        lambda: [
            {
                "title": "Upload Lesson Plans",
                "subtitle": f"Share files with other instructors at {facility.name if facility else 'your facility'}",
                "url": "#",
            },
            {
                "title": "Facility Roster",
                "subtitle": "See who else is teaching this session.",
                "url": "#",
            },
        ],
    )


def get_facility_metrics(facility: Facility | None):
    if not facility:
        return []
    key = shared_cache_key("facility_metrics", facility.pk)
    return cached(
        key,
        CACHE_TIMEOUT,
        lambda: [
            {"label": "Departments", "value": facility.departments.count()},
            {"label": "Faculty", "value": facility.facultyprofile_set.count()},
        ],
    )


def get_facility_overview_text(facility: Facility | None):
    if not facility:
        return "Customize this dashboard by wiring widgets that highlight occupancy, schedules, or outstanding actions for your facility team."
    dept_count = facility.departments.count()
    faculty_count = facility.facultyprofile_set.count()
    return (
        f"{facility.name} currently has {dept_count} departments and {faculty_count} active faculty members."
    )


def get_faction_enrollment_counts(faction: Faction):
    if not faction:
        return []
    key = shared_cache_key("leader_enrollments", faction.pk)
    return cached(
        key,
        CACHE_TIMEOUT,
        lambda: [
            {"label": item["faction__name"], "count": item["count"]}
            for item in faction.faction_enrollments.values("faction__name")
            .annotate(count=Count("id"))
            .order_by("faction__name")
        ],
    )


def get_attendee_schedule(profile, faction_enrollment=None):
    if not profile:
        return AttendeeClassEnrollment.objects.none()

    if faction_enrollment is None:
        enrollment = profile.enrollments.first()
        if enrollment:
            faction_enrollment = enrollment.faction_enrollment

    if not faction_enrollment:
        return AttendeeClassEnrollment.objects.none()

    return AttendeeClassEnrollment.objects.filter(
        attendee=profile,
        attendee_enrollment__faction_enrollment=faction_enrollment,
    )


def get_faculty_schedule(profile, facility_enrollment=None):
    if not profile:
        return FacultyEnrollment.objects.none()

    if facility_enrollment is None:
        enrollment = profile.enrollments.first()
        if enrollment:
            facility_enrollment = enrollment.facility_enrollment

    qs = FacultyEnrollment.objects.filter(faculty=profile)
    if facility_enrollment:
        qs = qs.filter(facility_enrollment=facility_enrollment)

    return qs.select_related("facility_enrollment", "facility_enrollment__facility")
