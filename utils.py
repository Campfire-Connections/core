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
            data = [
                ("Enrollments", "#", user.attendeeprofile_profile.enrollments.count(), 'count', 'count'),
                ("Messages", "#", user.attendeeprofile_profile.messages.count(), 'count', 'count'),
                ("ToDo", "#", user.attendeeprofile_profile.todo.count(), 'count', 'count'),
            ]
        elif user.user_type == User.UserType.LEADER:
            data = [
                ("Enrollments", "#", user.leaderprofile_profile.enrollments.count(), 'count', 'count'),
                ("Messages", "#", user.leaderprofile_profile.messages.count(), 'count', 'count'),
                ("ToDo", "#", user.leaderprofile_profile.achievements.count(), 'count', 'count'),
            ]
        elif user.user_type == User.UserType.FACULTY:
            msgs = 0 # user.facultyprofile_profile.messages.count()
            todo = 0 # user.facultyprofile_profile.todo.count()
            data = [
                ("Enrollments", "#", user.facultyprofile_profile.enrollments.count(), 'count first', 'count first'),
                ("Messages", "#", msgs, 'count', 'count'),
                ("ToDo", "#", todo, 'count', 'count'),
            ]
        else:
            data = []
        cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes

    return data
