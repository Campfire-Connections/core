# core/menu.py

# Menu for Faculty Admin
FACULTY_ADMIN_MENU = [
    # {"name": "Dashboard", "url_name": "dashboard", "icon": "fa-dashboard"},
    {
        "name": "Faculty Management",
        "url_name": "facultys:manage",
        "icon": "fa-users",
        "sub_items": [
            {"name": "Add Faculty", "url_name": "facultys:new"},
            {"name": "Assign Classes", "url_name": "home"},
        ],
    },
    {
        "name": "Class Management",
        "url_name": "home",
        "icon": "fa-book",
        "sub_items": [
            {"name": "View Classes", "url_name": "home"},
            {"name": "Create/Edit Classes", "url_name": "home"},
            {"name": "Class Enrollments", "url_name": "home"},
        ],
    },
    {
        "name": "Facility Management",
        "url_name": "facilities:manage",
        "icon": "fa-building",
        "sub_items": [
            {
                "name": "Department Management",
                "url_name": "departments:index_by_facility",
                "dynamic_params": {"slug": "user.facultyprofile.facility.slug"},
            },
            {
                "name": "Quarters Management",
                "url_name": "quarters:index_by_facility",
                "dynamic_params": {"slug": "user.facultyprofile.facility.slug"},
            },
        ],
    },
    {"name": "Reports", "url_name": "home", "icon": "fa-file"},
]

# Menu for Attendees
ATTENDEE_MENU = [
    # {"name": "Dashboard", "url_name": "dashboard", "icon": "fa-dashboard"},
    {
        "name": "My Schedule",
        "url_name": "attendees:enrollment:index_by_attendee",
        "dynamic_params": {
            "slug": "user.slug"
        },
        "icon": "fa-calendar",
    },
    {
        "name": "Courses",
        "url_name": "course_index",
        "icon": "fa-book",
        "sub_items": [
            {"name": "View Courses", "url_name": "view_courses"},
            {"name": "Enroll in Courses", "url_name": "enroll_courses"},
        ],
    },
    {"name": "Resources", "url_name": "resources", "icon": "fa-folder"},
    #{"name": "Notifications", "url_name": "notifications", "icon": "fa-bell"},
]

# Menu for Leaders
LEADER_MENU = [
    # {"name": "Dashboard", "url_name": "dashboard", "icon": "fa-dashboard"},
    {"name": "Reports", "url_name": "reports", "icon": "fa-file"},
]

# Menu for Leader Admin
LEADER_ADMIN_MENU = [
    # {"name": "Dashboard", "url_name": "dashboard", "icon": "fa-dashboard"},
    {
        "name": "Faction Management",
        "url_name": "factions:manage",
        "icon": "fa-users",
    },
    {
        "name": "Leader Management",
        "url_name": "leaders:index",
        "icon": "fa-users",
        "sub_items": [
            {"name": "View Leaders", "url_name": "view_leaders"},
            {"name": "Add/Edit Leaders", "url_name": "edit_leaders"},
            {"name": "Assign Tasks", "url_name": "assign_tasks"},
        ],
    },
    {"name": "Reports", "url_name": "reports", "icon": "fa-file"},
]

# Menu for Faculty
FACULTY_MENU = [
    # {"name": "Dashboard", "url_name": "dashboard", "icon": "fa-dashboard"},
    {"name": "My Classes", "url_name": "home", "icon": "fa-book"},
    {"name": "My Enrollments", "url_name": "home", "icon": "fa-tasks"},
    {"name": "Resources", "url_name": "home", "icon": "fa-folder"},
]

# Menu for Organization Faculty
ORGANIZATION_FACULTY_MENU = [
    # {"name": "Dashboard", "url_name": "dashboard", "icon": "fa-dashboard"},
    {
        "name": "Organization Management",
        "url_name": "organization_management",
        "icon": "fa-building",
        "sub_items": [
            {"name": "View Organization", "url_name": "view_organization"},
            {"name": "Manage Departments", "url_name": "manage_departments"},
        ],
    },
    {"name": "Reports", "url_name": "reports", "icon": "fa-file"},
]

toplinks = [
    {"title": "Help", "url_name": "help", "icon": "fa-circle-question"},
    {"title": "Sign Up", "url_name": "register", "visible_to": "guest"},
    {"title": "Sign In", "url_name": "login", "visible_to": "guest"},
    {
        "title": "Settings",
        "url_name": "account_settings",
        "visible_to": "authenticated",
        "icon": "fa-gears",
    },
    #        {"title": "Sign Out", "url_name": "signout", "visible_to": "authenticated"},
]
