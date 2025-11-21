from django.urls import reverse, NoReverseMatch


def user_is_admin(user):
    return getattr(user, "is_admin", False)


def resolve_context(base_context, dotted_path):
    if not dotted_path:
        return None
    value = base_context
    for attr in dotted_path.split("."):
        if value is None:
            return None
        if isinstance(value, dict):
            value = value.get(attr)
        else:
            value = getattr(value, attr, None)
    return value


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
            "key": "attendee_portal",
            "label": "My Profile",
            "icon": "fas fa-user",
            "children": [
                {
                    "key": "attendee_schedule",
                    "label": "My Schedule",
                    "icon": "fas fa-calendar",
                    "url_name": "attendees:enrollments:index",
                    "dynamic_kwargs": {"slug": "profile.slug"},
                },
                {
                    "key": "attendee_enrollments",
                    "label": "My Enrollments",
                    "icon": "fas fa-user-check",
                    "url_name": "attendees:enrollments:index",
                    "dynamic_kwargs": {"slug": "profile.slug"},
                },
                {
                    "key": "attendee_resources",
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
            "key": "leader_portal",
            "label": "Faction Mgmt",
            "icon": "fas fa-users",
            "children": [
                {
                    "key": "leader_roster",
                    "label": "View Roster",
                    "icon": "fas fa-users",
                    "url_name": "leaders:index",
                },
                {
                    "key": "leader_enrollments",
                    "label": "Manage Enrollments",
                    "icon": "fas fa-calendar-alt",
                    "url_name": "factions:enrollments:index",
                    "dynamic_kwargs": {"slug": "profile.faction.slug"},
                },
                {
                    "key": "leader_resources",
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
                    "key": "faculty_schedule",
                    "label": "My Schedule",
                    "icon": "fas fa-calendar",
                    "url_name": "facultys:manage",
                },
                {
                    "key": "faculty_enrollments",
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
            "condition": user_is_admin,
            "children": [
                {
                    "key": "faculty_new",
                    "label": "New Faculty",
                    "icon": "fas fa-plus-square",
                    "url_name": "facilities:facultys:new",
                    "dynamic_kwargs": {"facility_slug": "profile.facility.slug"},
                },
                {
                    "key": "faculty_manage",
                    "label": "Manage Faculty",
                    "icon": "fas fa-users-cog",
                    "url_name": "facilities:faculty:manage",
                    "dynamic_kwargs": {"facility_slug": "profile.facility.slug"},
                },
                {
                    "key": "faculty_reports",
                    "label": "Reports",
                    "icon": "fas fa-chart-bar",
                    "url_name": "reports:list_user_reports",
                },
            ],
        },
        {
            "key": "faculty_quick",
            "label": "Faculty Dashboard",
            "icon": "fas fa-graduation-cap",
            "url_name": "facultys:manage",
            "group": "quick",
        },
    ],
    "ADMIN": [
        {
            "key": "admin_tools",
            "label": "Admin Tools",
            "icon": "fas fa-tools",
            "children": [
                {
                    "key": "admin_site",
                    "label": "Django Admin",
                    "icon": "fas fa-shield-alt",
                    "url_name": "admin:index",
                },
                {
                    "key": "admin_users",
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

# Organization faculty shares faculty menu
MENU_REGISTRY["ORGANIZATION_FACULTY"] = MENU_REGISTRY["FACULTY"]


def get_menu_definitions(user):
    user_type = getattr(user, "user_type", "other").upper()
    entries = []
    entries.extend(MENU_REGISTRY.get("COMMON", []))
    entries.extend(MENU_REGISTRY.get(user_type, []))
    return entries


def clone_entry(entry):
    return {
        "key": entry.get("key"),
        "label": entry.get("label"),
        "icon": entry.get("icon"),
        "url": entry.get("url"),
        "children": entry.get("children", []),
    }


def flatten_definitions(definitions):
    flat = {}
    for definition in definitions:
        key = definition.get("key")
        if key:
            flat[key] = definition
        for child in definition.get("children", []):
            flat.update(flatten_definitions([child]))
    return flat


def build_menu_for_user(user, favorites=None):
    favorites = favorites or []
    profile = getattr(user, "get_profile", lambda: None)()
    base_context = {"user": user, "profile": profile}
    definitions = get_menu_definitions(user)
    flat_defs = flatten_definitions(definitions)

    primary = []
    quick = []
    quick_keys = set()

    for definition in definitions:
        entry = resolve_entry(definition, base_context)
        if not entry:
            continue
        if definition.get("group") == "quick":
            quick.append(entry)
            if entry.get("key"):
                quick_keys.add(entry["key"])
        else:
            primary.append(entry)

    for key in favorites:
        if key in quick_keys:
            continue
        definition = flat_defs.get(key)
        if not definition:
            continue
        entry = resolve_entry(definition, base_context)
        if entry and entry.get("url"):
            entry = clone_entry(entry)
            entry["favorite"] = True
            quick.append(entry)
            quick_keys.add(key)

    return {"primary": primary, "quick": quick}


def resolve_entry(definition, base_context):
    condition = definition.get("condition")
    if condition and not condition(base_context["user"]):
        return None

    url = resolve_url(definition, base_context)
    children = []
    for child_def in definition.get("children", []):
        child_entry = resolve_entry(child_def, base_context)
        if child_entry:
            children.append(child_entry)

    return {
        "key": definition.get("key"),
        "label": definition.get("label"),
        "icon": definition.get("icon"),
        "url": url,
        "children": children,
    }


def resolve_url(definition, base_context):
    url_name = definition.get("url_name")
    if not url_name:
        return None
    kwargs = {}
    for key, path in definition.get("dynamic_kwargs", {}).items():
        kwargs[key] = resolve_context(base_context, path)
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        if kwargs:
            return reverse(url_name, kwargs=kwargs)
        return reverse(url_name)
    except NoReverseMatch:
        return None
