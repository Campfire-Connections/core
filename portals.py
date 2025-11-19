"""Portal registry defining dashboards, widgets, and permissions per role."""

PORTALS = {
    "organization": {
        "label": "Organization Admin",
        "dashboard_template": "organization/dashboard.html",
        "widgets": ["org_overview", "org_activity"],
        "allowed_user_types": ["ADMIN", "ORGANIZATION_FACULTY"],
    },
    "facility": {
        "label": "Facility Admin",
        "dashboard_template": "facility/dashboard.html",
        "widgets": ["facility_overview", "facility_classes"],
        "allowed_user_types": ["FACILITY_FACULTY", "FACULTY"],
    },
    "faction": {
        "label": "Faction Leader",
        "dashboard_template": "faction/dashboard.html",
        "widgets": ["faction_overview", "faction_roster"],
        "allowed_user_types": ["LEADER"],
    },
    "attendee": {
        "label": "Attendee",
        "dashboard_template": "attendee/dashboard.html",
        "widgets": ["schedule_widget", "resources_widget"],
        "allowed_user_types": ["ATTENDEE"],
    },
    "faculty": {
        "label": "Faculty",
        "dashboard_template": "faculty/dashboard.html",
        "widgets": ["class_enrollments_widget", "resources_widget"],
        "allowed_user_types": ["FACULTY"],
    },
}


def get_portal_config(portal_key):
    """Safe lookup for portal configuration."""
    return PORTALS.get(portal_key, {})
