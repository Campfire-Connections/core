# core/utils.py

from django.core.cache import cache

from user.models import User

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
                ("Enrollments", "#", getattr(profile, "enrollments", []).count() if profile else 0, 'count', 'count'),
                ("Messages", "#", getattr(profile, "messages", []).count() if profile else 0, 'count', 'count'),
                ("ToDo", "#", getattr(profile, "todo", []).count() if profile else 0, 'count', 'count'),
            ]
        elif user.user_type == User.UserType.LEADER:
            profile = getattr(user, "leaderprofile_profile", None)
            data = [
                ("Enrollments", "#", getattr(profile, "enrollments", []).count() if profile else 0, 'count', 'count'),
                ("Messages", "#", getattr(profile, "messages", []).count() if profile else 0, 'count', 'count'),
                ("ToDo", "#", getattr(profile, "achievements", []).count() if profile else 0, 'count', 'count'),
            ]
        elif user.user_type == User.UserType.FACULTY:
            profile = getattr(user, "facultyprofile_profile", None)
            msgs = getattr(profile, "messages", []).count() if profile else 0
            todo = getattr(profile, "todo", []).count() if profile else 0
            data = [
                ("Enrollments", "#", getattr(profile, "enrollments", []).count() if profile else 0, 'count first', 'count first'),
                ("Messages", "#", msgs, 'count', 'count'),
                ("ToDo", "#", todo, 'count', 'count'),
            ]
        else:
            data = []
        cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes

    return data
