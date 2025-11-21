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
