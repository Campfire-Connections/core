from django.urls import reverse, NoReverseMatch


def is_admin(user):
    return getattr(user, "is_admin", False)


def get_profile(user):
    profile_getter = getattr(user, "get_profile", None)
    if callable(profile_getter):
        return profile_getter()
    return None


def resolve_context_path(base_context, path):
    if not path:
        return None
    parts = path.split(".")
    root = parts[0]
    current = base_context.get(root)
    for attr in parts[1:]:
        if current is None:
            return None
        current = getattr(current, attr, None)
    return current


MENU_REGISTRY = {
    "COMMON": [
        {
            "key": "dashboard",
            "label": "Dashboard",
            "icon": "fas fa-fire",
            "url_name": "dashboard",
        }
    ],
    "ATTENDEE": [
        {
            "key": "attendee_profile",
            "label": "My Profile",
            "icon": "fas fa-user",
            "children": [
                {
                    "label": "My Schedule",
                    "icon": "fas fa-calendar",
                    "url_name": "attendees:enrollments:index",
                    "dynamic_kwargs": {"slug": "profile.slug"},
                },
                {
                    "label": "My Enrollments",
                    "icon": "fas fa-user-check",
                    "url_name": "attendees:enrollments:index",
                    "dynamic_kwargs": {"slug": "profile.slug"},
                },
                {
                    "label": "Resources",
                    "icon": "fas fa-book",
                    "url_name": "resources",
                },
            ],
        },
        {
            "key": "attendee_quick",
            "label": "My Schedule",
            "icon": "fas fa-calendar",
            "url_name": "attendees:enrollments:index",
            "dynamic_kwargs": {"slug": "profile.slug"},
            "group": "quick",
        },
    ],
    "LEADER": [
        {
            "key": "faction_mgmt",
            "label": "Faction Mgmt",
            "icon": "fas fa-users",
            "children": [
                {
                    "label": "View Roster",
                    "icon": "fas fa-users",
                    "url_name": "leaders:index",
                },
                {
                    "label": "Manage Enrollments",
                    "icon": "fas fa-calendar-alt",
                    "url_name": "factions:enrollments:index",
                    "dynamic_kwargs": {"slug": "profile.faction.slug"},
                },
                {
                    "label": "Faction Resources",
                    "icon": "fas fa-book",
                    "url_name": "resources",
                },
            ],
        },
        {
            "key": "leader_quick",
            "label": "Faction Dashboard",
            "icon": "fas fa-bullseye",
            "url_name": "leaders:dashboard",
            "group": "quick",
        },
    ],
    "FACULTY": [
        {
            "key": "faculty_portal",
            "label": "Faculty Portal",
            "icon": "fas fa-chalkboard-teacher",
            "children": [
                {
                    "label": "My Schedule",
                    "icon": "fas fa-calendar",
                    "url_name": "facultys:manage",
                },
                {
                    "label": "My Enrollments",
                    "icon": "fas fa-user-check",
                    "url_name": "facultys:manage",
                },
            ],
        },
        {
            "key": "faculty_admin",
            "label": "Faculty Admin",
            "icon": "fas fa-user-cog",
            "condition": is_admin,
            "children": [
                {
                    "label": "New Faculty",
                    "icon": "fas fa-plus-square",
                    "url_name": "facilities:facultys:new",
                    "dynamic_kwargs": {
                        "facility_slug": "profile.facility.slug",
                    },
                },
                {
                    "label": "Manage Faculty",
                    "icon": "fas fa-users-cog",
                    "url_name": "facilities:faculty:manage",
                    "dynamic_kwargs": {
                        "facility_slug": "profile.facility.slug",
                    },
                },
                {
                    "label": "Reports",
                    "icon": "fas fa-chart-bar",
                    "url_name": "reports:list_user_reports",
                },
            ],
        },
        {
            "key": "faculty_quick",
            "label": "My Faculty Portal",
            "icon": "fas fa-graduation-cap",
            "url_name": "facultys:manage",
            "group": "quick",
        },
    ],
    "ADMIN": [
        {
            "key": "admin_tools",
            "label": "Admin",
            "icon": "fas fa-tools",
            "children": [
                {
                    "label": "Django Admin",
                    "icon": "fas fa-shield-alt",
                    "url_name": "admin:index",
                },
                {
                    "label": "User Management",
                    "icon": "fas fa-users-cog",
                    "url_name": "leaders:index",
                },
            ],
        },
        {
            "key": "admin_quick",
            "label": "Admin Site",
            "icon": "fas fa-lock",
            "url_name": "admin:index",
            "group": "quick",
        },
    ],
}

MENU_REGISTRY["ORGANIZATION_FACULTY"] = MENU_REGISTRY["FACULTY"]


def get_menu_definition_for_user(user):
    user_type = getattr(user, "user_type", "OTHER")
    user_type = user_type.upper()
    entries = []
    entries.extend(MENU_REGISTRY.get("COMMON", []))
    entries.extend(MENU_REGISTRY.get(user_type, []))
    return entries


def build_menu_for_user(user):
    primary = []
    quick = []
    profile = get_profile(user)
    base_context = {"user": user, "profile": profile}
    for definition in get_menu_definition_for_user(user):
        resolved = resolve_menu_entry(definition, base_context)
        if resolved:
            target = quick if definition.get("group") == "quick" else primary
            target.append(resolved)
    return {"primary": primary, "quick": quick}


def resolve_menu_entry(entry, base_context):
    condition = entry.get("condition")
    if condition and not condition(base_context["user"]):
        return None

    url = resolve_url(entry, base_context)
    children = []
    for child in entry.get("children", []):
        child_resolved = resolve_menu_entry(child, base_context)
        if child_resolved:
            children.append(child_resolved)

    return {
        "label": entry.get("label", entry.get("name")),
        "icon": entry.get("icon"),
        "url": url,
        "children": children,
    }


def resolve_url(entry, base_context):
    url_name = entry.get("url_name")
    if not url_name:
        return None
    kwargs = {}
    dynamic_kwargs = entry.get("dynamic_kwargs", {})
    for key, path in dynamic_kwargs.items():
        kwargs[key] = resolve_context_path(base_context, path)
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        if kwargs:
            return reverse(url_name, kwargs=kwargs)
        return reverse(url_name)
    except NoReverseMatch:
        return None
