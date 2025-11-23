# core/context_processors.py

import logging


from django.core.cache import cache
from django.db.models import Q
from django.urls import NoReverseMatch, reverse

from enrollment.models.facility import FacilityEnrollment
from enrollment.models.faction import FactionEnrollment
from core.utils import get_info_row_data, get_leader_profile, is_leader_admin
from enrollment.models.enrollment import ActiveEnrollment
from faction.models.faction import Faction
from types import SimpleNamespace

from organization.models import Organization
from user.models import User

from .menus import toplinks
from .menu_registry import build_menu_for_user
from core.models.navigation import NavigationPreference

logger = logging.getLogger(__name__)


def dynamic_menu(request):
    if not request.user.is_authenticated:
        return {
            "menu_items": [],
            "quick_menu_items": [],
            "favorite_menu_keys": [],
            "toggle_nav_favorite_url": "",
        }

    try:
        preferences = request.user.navigation_preference
    except NavigationPreference.DoesNotExist:
        preferences = NavigationPreference.objects.create(user=request.user)

    favorites = list(preferences.favorite_keys or [])
    menu = build_menu_for_user(request.user, favorites=favorites)
    try:
        toggle_url = reverse("toggle_nav_favorite")
    except NoReverseMatch:
        toggle_url = ""
    return {
        "menu_items": menu.get("primary", []),
        "quick_menu_items": menu.get("quick", []),
        "favorite_menu_keys": favorites,
        "toggle_nav_favorite_url": toggle_url,
    }


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
    active_enrollment = ActiveEnrollment()
    active_enrollment_id = request.session.get("active_enrollment_id")
    if active_enrollment_id:
        active_enrollment = (
            ActiveEnrollment.objects.filter(id=active_enrollment_id).first()
            or active_enrollment
        )
    elif request.user.is_authenticated:
        active_enrollment = (
            ActiveEnrollment.objects.filter(user_id=request.user.id).first()
            or ActiveEnrollment(user_id=request.user.id)
        )
    if (
        request.user.is_authenticated
        and not getattr(active_enrollment, "user_id", None)
    ):
        active_enrollment.user_id = request.user.id

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
    elif is_leader_admin(user):
        leader_profile = get_leader_profile(user)

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
