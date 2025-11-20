# core/context_processors.py

import logging


from django.core.cache import cache
from django.db.models import Q

from enrollment.models.facility import FacilityEnrollment
from enrollment.models.faction import FactionEnrollment
from core.utils import get_info_row_data
from enrollment.models.enrollment import ActiveEnrollment
from faction.models.faction import Faction
from types import SimpleNamespace

from organization.models import Organization
from user.models import User

from .menus import (
    FACULTY_ADMIN_MENU,
    ATTENDEE_MENU,
    LEADER_MENU,
    LEADER_ADMIN_MENU,
    FACULTY_MENU,
    ORGANIZATION_FACULTY_MENU,
    toplinks,
)

logger = logging.getLogger(__name__)


def build_dynamic_url(item, user):
    if "dynamic_params" in item:
        for key, path in item["dynamic_params"].items():
            if path:
                logger.debug(f"Processing dynamic param: {path}")
                value = user
                for attr in path.split("."):
                    value = getattr(value, attr, None)
                    if value is None:
                        logger.warning(f"Attribute '{attr}' in '{path}' is None.")
                        break
                item["dynamic_params"][key] = value
            else:
                logger.warning(f"Dynamic param for key '{key}' is None.")
                item["dynamic_params"][key] = None
    return item


def dynamic_menu(request):
    menu = []
    if request.user.is_authenticated:
        user = request.user
        user_type = user.user_type
        menu_mapping = {
            "FACULTY": FACULTY_MENU,
            "ATTENDEE": ATTENDEE_MENU,
            "LEADER": LEADER_MENU,
            "ORGANIZATION_FACULTY": ORGANIZATION_FACULTY_MENU,
        }
        if user_type == "FACULTY" and user.is_admin:
            menu = FACULTY_ADMIN_MENU.copy()
        elif user_type == "LEADER" and user.is_admin:
            menu = LEADER_ADMIN_MENU.copy()
        else:
            menu = menu_mapping.get(user_type, []).copy()

        context = {"user": user}
        # Add any additional context needed for dynamic params
        if hasattr(user, "facultyprofile"):
            context["faculty_slug"] = user.facultyprofile.facility.slug

        for item in menu:
            item = build_dynamic_url(item, user)

            if "sub_items" in item:
                for sub_item in item["sub_items"]:
                    sub_item = build_dynamic_url(sub_item, user)

        logger.debug(f"menu: {menu}")

    return {"menu_items": menu}


def top_links_menu(request):
    context = {"toplinks": toplinks}
    logger.debug("Top links menu context: %s", context)
    return context


def user_type(request):
    return {
        "user_type": (
            request.user.user_type if request.user.is_authenticated else "other"
        )
    }


def user_profile(request):
    if not request.user.is_authenticated:
        return {"user_profile": None}

    profile = request.user.get_profile()
    if profile:
        return {"user_profile": profile}

    fallback_org = Organization.objects.order_by("id").first()
    placeholder = SimpleNamespace(
        slug="",
        organization=fallback_org,
        user=request.user,
    )
    return {"user_profile": placeholder}


def active_enrollment(request):
    if request.user.is_superuser:
        return {}
    if active_enrollment_id := request.session.get("active_enrollment_id"):
        active_enrollment = ActiveEnrollment.objects.get(id=active_enrollment_id)
    elif request.user.is_authenticated:
        active_enrollment = ActiveEnrollment.objects.get(
            user_id=request.user.id
        ) or ActiveEnrollment(user_id=request.user.id)
    else:
        active_enrollment = ActiveEnrollment()
    faction_enrollment = active_enrollment.faction_enrollment or {}
    if faction_enrollment:
        faction_id = active_enrollment.faction_enrollment.faction.id or 0
        faction = (
            Faction.objects.with_member_count()
            .with_sub_faction_count()
            .get(id=faction_id)
        )
        active_enrollment.faction_enrollment.faction = faction

    return {"active_enrollment": active_enrollment}


def color_scheme_processor(request):
    """Returns a dictionary containing the color scheme for the website."""

    warm_orange = "#ea6900"
    deep_red = "#cc2500"
    earthy_brown = "#612809"
    creamy_white = "#fff8db"
    forest_green = "#556643"
    dark_charcoal = "#00100c"

    highlight = warm_orange
    call_to_action = deep_red
    bg_dk = earthy_brown
    bg_lt = creamy_white
    secondary = forest_green
    text = dark_charcoal

    colors = {
        "text": text,
        "bg_lt": bg_lt,
        "bg_dk": bg_dk,
        "secondary_highlight": secondary,
        "call_to_action": call_to_action,
        "primary": highlight,
    }

    return {"color_scheme": colors}


def user_info_row(request):
    """
    Adds the user's info row data to the template context for authenticated users.
    """
    if request.user.is_authenticated:
        return {"info_row_data": get_info_row_data(request.user)}
    return {}



def my_enrollments(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user
    profile = user_profile(request)
    
    enrollments = {
        "facility_enrollments": [],
        "faction_enrollments": [],
        "can_enroll_self": False,
        "can_enroll_faction": False,
    }

    # Attendee: Fetch personal enrollments
    if user.user_type == "ATTENDEE":
        attendee_profile = getattr(user, "attendeeprofile_profile", None)

        if attendee_profile:
            # Fetch the faction associated with the attendee
            faction = attendee_profile.faction

            # Facility enrollments via faction -> faction enrollments -> facility enrollments
            if faction:
                enrollments["facility_enrollments"] = FacilityEnrollment.objects.filter(
                    id__in=faction.enrollments.values_list("facility_enrollment_id", flat=True)
                )

                enrollments["faction_enrollments"] = FactionEnrollment.objects.filter(
                    faction=faction
                )
            else:
                # If no faction, set empty QuerySets
                enrollments["facility_enrollments"] = FacilityEnrollment.objects.none()
                enrollments["faction_enrollments"] = FactionEnrollment.objects.none()

            # Can enroll self
            enrollments["can_enroll_self"] = True
        else:
            # Handle cases where the attendee has no profile
            enrollments["facility_enrollments"] = FacilityEnrollment.objects.none()
            enrollments["faction_enrollments"] = FactionEnrollment.objects.none()
            enrollments["can_enroll_self"] = False

    # Leader Admin: Fetch faction enrollments
    elif user.user_type == "LEADER" and user.is_admin:

        leader_profile = getattr(user, "leaderprofile_profile", None)

        if leader_profile:
            # Fetch the faction associated with the leader
            faction = leader_profile.faction

            # Facility enrollments via faction -> faction enrollments -> facility enrollments
            if faction:
                enrollments["facility_enrollments"] = FacilityEnrollment.objects.filter(
                    id__in=faction.enrollments.values_list("facility_enrollment_id", flat=True)
                )

                enrollments["faction_enrollments"] = FactionEnrollment.objects.filter(
                    faction=faction
                )
            else:
                # If no faction, set empty QuerySets
                enrollments["facility_enrollments"] = FacilityEnrollment.objects.none()
                enrollments["faction_enrollments"] = FactionEnrollment.objects.none()

            # Can enroll self
            enrollments["can_enroll_self"] = True
        else:
            # Handle cases where the leader has no profile
            enrollments["facility_enrollments"] = FacilityEnrollment.objects.none()
            enrollments["faction_enrollments"] = FactionEnrollment.objects.none()
            enrollments["can_enroll_self"] = False

    return {"my_enrollments": enrollments}
