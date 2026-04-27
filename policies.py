from user.models import User


def is_admin_user(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_admin", False)
            or getattr(user, "user_type", None) == User.UserType.ADMIN
        )
    )


def user_profile(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None
    get_profile = getattr(user, "get_profile", None)
    if callable(get_profile):
        return get_profile()
    return None


def visible_facilities_for_user(user):
    from facility.models.facility import Facility

    if is_admin_user(user):
        return Facility.objects.all()

    profile = user_profile(user)
    facility_id = getattr(profile, "facility_id", None)
    if facility_id:
        return Facility.objects.filter(id=facility_id)

    organization_id = getattr(profile, "organization_id", None)
    if organization_id:
        return Facility.objects.filter(organization_id=organization_id)

    return Facility.objects.none()


def can_view_facility(user, facility):
    if not facility:
        return False
    return visible_facilities_for_user(user).filter(id=facility.id).exists()


def can_manage_facility(user, facility):
    from core.utils import is_faculty_admin

    return bool(is_admin_user(user) or (is_faculty_admin(user) and can_view_facility(user, facility)))


def _faction_descendant_ids(faction):
    ids = []
    stack = [faction]
    while stack:
        current = stack.pop()
        ids.append(current.id)
        stack.extend(list(current.children.filter(is_deleted=False)))
    return ids


def visible_factions_for_user(user):
    from faction.models.faction import Faction

    base = Faction.objects.filter(is_deleted=False)
    if is_admin_user(user):
        return base

    profile = user_profile(user)
    faction = getattr(profile, "faction", None)
    if faction:
        return base.filter(id__in=_faction_descendant_ids(faction))

    organization_id = getattr(profile, "organization_id", None)
    if organization_id:
        return base.filter(organization_id=organization_id)

    return base.none()


def can_view_faction(user, faction):
    if not faction:
        return False
    return visible_factions_for_user(user).filter(id=faction.id).exists()


def can_manage_faction(user, faction):
    from core.utils import is_leader_admin

    return bool(is_admin_user(user) or (is_leader_admin(user) and can_view_faction(user, faction)))
