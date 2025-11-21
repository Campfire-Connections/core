from django.core.cache import cache
from django.db.models import Count

from faction.models import Faction
from facility.models import Facility
from enrollment.models.attendee_class import AttendeeClassEnrollment
from enrollment.models.faculty import FacultyEnrollment
from course.models.facility_class import FacilityClass

CACHE_TIMEOUT = 60 * 5


def cache_key(prefix, identifier):
    return f"dashboard:{prefix}:{identifier}"


def get_leader_metrics(faction: Faction):
    if not faction:
        return []
    key = cache_key("leader_metrics", faction.pk)
    metrics = cache.get(key)
    if metrics is None:
        metrics = [
            {"label": "Leaders", "value": faction.member_count(user_type="leader")},
            {"label": "Attendees", "value": faction.member_count(user_type="attendee")},
            {"label": "Sub-factions", "value": faction.children.count()},
        ]
        cache.set(key, metrics, CACHE_TIMEOUT)
    return metrics


def get_leader_resource_links(faction: Faction | None):
    key = cache_key("leader_resources", faction.pk if faction else "global")
    resources = cache.get(key)
    if resources is None:
        resources = [
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
        ]
        cache.set(key, resources, CACHE_TIMEOUT)
    return resources


def get_attendee_resources(faction: Faction | None):
    key = cache_key("attendee_resources", faction.pk if faction else "global")
    resources = cache.get(key)
    if resources is None:
        resources = [
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
        ]
        cache.set(key, resources, CACHE_TIMEOUT)
    return resources


def get_attendee_announcements(faction: Faction | None):
    key = cache_key("attendee_announcements", faction.pk if faction else "global")
    announcements = cache.get(key)
    if announcements is None:
        name = faction.name if faction else "camp"
        announcements = [
            {
                "title": "Welcome to {}".format(name),
                "subtitle": "Orientation starts Monday at 9am.",
                "meta": "",
            },
            {
                "title": "Don't forget lights-out",
                "subtitle": "Quiet hours begin at 10pm.",
                "meta": "",
            },
        ]
        cache.set(key, announcements, CACHE_TIMEOUT)
    return announcements


def get_faculty_resources(facility: Facility | None):
    key = cache_key("faculty_resources", facility.pk if facility else "global")
    resources = cache.get(key)
    if resources is None:
        name = facility.name if facility else "your facility"
        resources = [
            {
                "title": "Upload Lesson Plans",
                "subtitle": f"Share files with other instructors at {name}",
                "url": "#",
            },
            {
                "title": "Facility Roster",
                "subtitle": "See who else is teaching this session.",
                "url": "#",
            },
        ]
        cache.set(key, resources, CACHE_TIMEOUT)
    return resources


def get_facility_metrics(facility: Facility | None):
    if not facility:
        return []
    key = cache_key("facility_metrics", facility.pk)
    metrics = cache.get(key)
    if metrics is None:
        metrics = [
            {"label": "Departments", "value": facility.departments.count()},
            {"label": "Faculty", "value": facility.facultyprofile_set.count()},
        ]
        cache.set(key, metrics, CACHE_TIMEOUT)
    return metrics


def get_faction_enrollment_counts(faction: Faction):
    if not faction:
        return []
    key = cache_key("leader_enrollments", faction.pk)
    data = cache.get(key)
    if data is None:
        enrollments = (
            faction.faction_enrollments.values("faction__name")
            .annotate(count=Count("id"))
            .order_by("faction__name")
        )
        data = [
            {"label": item["faction__name"], "count": item["count"]}
            for item in enrollments
        ]
        cache.set(key, data, CACHE_TIMEOUT)
    return data


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
