# core/utils.py

from django.core.cache import cache

from user.models import User


def _safe_count(value):
    if value is None:
        return 0
    count_attr = getattr(value, "count", None)
    if callable(count_attr):
        try:
            return count_attr()
        except TypeError:
            pass
    try:
        return len(value)
    except TypeError:
        return 0

def get_info_row_data(user):
    """Retrieves cached dashboard information rows for different user types.

        Generates a list of key metrics based on the user's role, with caching to improve 
        performance.

        Args:
            user: The user instance for which to retrieve dashboard information.

        Returns:
            list: A list of tuples containing dashboard metrics (label, link, count).
        """

    cache_key = f"info_row_data_{user.id}"
    data = cache.get(cache_key)

    if not data:
        if user.user_type == User.UserType.ATTENDEE:
            profile = getattr(user, "attendeeprofile_profile", None)
            data = [
                ("Enrollments", "#", _safe_count(getattr(profile, "enrollments", None)), "count", "count"),
                ("Messages", "#", _safe_count(getattr(profile, "messages", None)), "count", "count"),
                ("ToDo", "#", _safe_count(getattr(profile, "todo", None)), "count", "count"),
            ]
        elif user.user_type == User.UserType.LEADER:
            profile = getattr(user, "leaderprofile_profile", None)
            data = [
                ("Enrollments", "#", _safe_count(getattr(profile, "enrollments", None)), "count", "count"),
                ("Messages", "#", _safe_count(getattr(profile, "messages", None)), "count", "count"),
                ("ToDo", "#", _safe_count(getattr(profile, "achievements", None)), "count", "count"),
            ]
        elif user.user_type == User.UserType.FACULTY:
            profile = getattr(user, "facultyprofile_profile", None)
            msgs = _safe_count(getattr(profile, "messages", None))
            todo = _safe_count(getattr(profile, "todo", None))
            data = [
                ("Enrollments", "#", _safe_count(getattr(profile, "enrollments", None)), 'count first', 'count first'),
                ("Messages", "#", msgs, 'count', 'count'),
                ("ToDo", "#", todo, 'count', 'count'),
            ]
        else:
            data = []
        cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes

    return data


def get_leader_profile(user):
    """Safely retrieve the leader profile from a user instance."""
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "leaderprofile_profile", None) or getattr(user, "leaderprofile", None)


def is_leader_admin(user):
    """Determine if the given user is a faction leader with admin privileges."""
    if not user or getattr(user, "user_type", None) != User.UserType.LEADER:
        return False
    if getattr(user, "is_superuser", False):
        return True
    profile = get_leader_profile(user)
    return bool(getattr(profile, "is_admin", False) or getattr(user, "is_admin", False))


def get_faculty_profile(user):
    """Safely retrieve the faculty profile from a user instance."""
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "facultyprofile_profile", None) or getattr(user, "facultyprofile", None)


def is_faculty_admin(user):
    """
    Determine if the given user is a faculty admin (facility-level).
    Preference is given to the FacultyProfile role flag; falls back to user.is_admin.
    """
    if not user or getattr(user, "user_type", None) not in (
        User.UserType.FACULTY,
        User.UserType.FACILITY_FACULTY,
    ):
        return False
    if getattr(user, "is_superuser", False):
        return True
    profile = get_faculty_profile(user)
    if profile and getattr(profile, "is_facility_admin", False):
        return True
    return bool(getattr(user, "is_admin", False))


def is_department_admin(user):
    """Check if the user is faculty with department oversight privileges."""
    if not user or getattr(user, "user_type", None) not in (
        User.UserType.FACULTY,
        User.UserType.FACILITY_FACULTY,
    ):
        return False
    profile = get_faculty_profile(user)
    return bool(profile and getattr(profile, "is_department_admin", False))
