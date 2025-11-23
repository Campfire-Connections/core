"""
Management command to seed a coherent, deterministic test dataset that spans the
major Campfire Connections domain apps.
"""

from contextlib import contextmanager
from datetime import date, time, timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save

from organization.models import Organization
from facility.models import Facility, Department, QuartersType, Quarters, FacultyProfile
from faction.models import Faction, LeaderProfile, AttendeeProfile
from course.models.course import Course
from course.models.requirement import Requirement
from course.models.facility_class import FacilityClass
from enrollment.models.organization import OrganizationEnrollment, OrganizationCourse
from enrollment.models.facility import FacilityEnrollment
from enrollment.models.temporal import Week, Period
from enrollment.models.facility_class import FacilityClassEnrollment
from enrollment.models.faction import FactionEnrollment
from enrollment.models.availability import QuartersWeekAvailability
from enrollment.models.faculty import FacultyEnrollment as FacultyEnrollmentRecord
from enrollment.models.leader import LeaderEnrollment as LeaderEnrollmentRecord
from enrollment.models.attendee import AttendeeEnrollment as AttendeeEnrollmentRecord
from enrollment.models.enrollment import ActiveEnrollment, Enrollment as GenericEnrollment
from user.models import User, ensure_profile


@contextmanager
def muted_profile_signals():
    """Temporarily disconnect profile signals so we can assign relationships manually."""

    receivers = [
        ensure_profile,
    ]
    for receiver in receivers:
        post_save.disconnect(receiver, sender=User)
    try:
        yield
    finally:
        for receiver in receivers:
            post_save.connect(receiver, sender=User)


class Command(BaseCommand):
    help = "Populate the database with a curated, repeatable collection of test data."

    def handle(self, *args, **options):
        builder = TestDataBuilder(self)
        with transaction.atomic():
            builder.build()
        self.stdout.write(self.style.SUCCESS("Seed data ready."))


class TestDataBuilder:
    """Imperative helper that wires up all of the related domain objects."""

    def __init__(self, command: BaseCommand):
        self.command = command
        self.orgs = {}
        self.facilities = {}
        self.departments = {}
        self.quarters_types = {}
        self.quarters = {}
        self.factions = {}
        self.requirements = {}
        self.courses = {}
        self.organization_enrollments = {}
        self.organization_courses = {}
        self.facility_enrollments = {}
        self.weeks = {}
        self.periods = {}
        self.facility_classes = {}
        self.class_enrollments = {}
        self.users = {}
        self.leader_profiles = {}
        self.attendee_profiles = {}
        self.faculty_profiles = {}
        self.faction_enrollments = {}
        self.leader_enrollments = {}
        self.attendee_enrollments = {}
        self.faculty_enrollments = {}

    def build(self):
        self._log("Creating organizations")
        self._create_organizations()

        self._log("Creating facilities, departments, and quarters")
        self._create_facilities_and_departments()
        self._create_quarters()

        self._log("Creating factions")
        self._create_factions()

        self._log("Creating requirements and courses")
        self._create_courses()

        self._log("Creating enrollments and schedules")
        self._create_organization_enrollments()
        self._create_facility_enrollments()
        self._create_facility_classes()

        self._log("Creating users and profiles")
        self._create_users_and_profiles()

        self._log("Creating faction enrollments and personal assignments")
        # Clear any existing quarters reservations to avoid conflicts on upsert
        QuartersWeekAvailability.objects.all().delete()
        self._create_faction_enrollments()
        self._create_person_enrollments()

    def _log(self, message, style=None):
        writer = self.command.stdout.write
        if style:
            writer(style(message))
        else:
            writer(message)

    def _upsert(self, model, lookup, defaults, label=None):
        obj, created = model.objects.update_or_create(defaults=defaults, **lookup)
        action = "created" if created else "updated"
        if label is None:
            label = defaults.get("name") or lookup
        self._log(f"  - {model.__name__} {label} {action}")
        return obj

    def _create_organizations(self):
        national = self._upsert(
            Organization,
            {"name": "Campfire National Council"},
            {
                "slug": "campfire-national-council",
                "abbreviation": "CNC",
                "description": "National umbrella for all councils.",
                "max_depth": 5,
                "parent": None,
            },
            label="Campfire National Council",
        )
        northern = self._upsert(
            Organization,
            {"name": "Northern Lights Council"},
            {
                "slug": "northern-lights-council",
                "abbreviation": "NLC",
                "description": "Regional council serving the northern territories.",
                "max_depth": 4,
                "parent": national,
            },
            label="Northern Lights Council",
        )
        cascade = self._upsert(
            Organization,
            {"name": "Cascade District"},
            {
                "slug": "cascade-district",
                "abbreviation": "CD",
                "description": "District focused on mountain and river programs.",
                "max_depth": 3,
                "parent": northern,
            },
            label="Cascade District",
        )

        self.orgs.update(
            {
                "national": national,
                "northern": northern,
                "cascade": cascade,
            }
        )

    def _create_facilities_and_departments(self):
        cascade = self.orgs["cascade"]
        river_bend = self._upsert(
            Facility,
            {"name": "River Bend Training Center"},
            {
                "slug": "river-bend-training-center",
                "description": "Primary high-adventure campus hugging the river.",
                "organization": cascade,
                "parent": None,
            },
            label="River Bend Training Center",
        )
        summit_ridge = self._upsert(
            Facility,
            {"name": "Summit Ridge Basecamp"},
            {
                "slug": "summit-ridge-basecamp",
                "description": "Remote alpine facility used for leadership intensives.",
                "organization": cascade,
                "parent": None,
            },
            label="Summit Ridge Basecamp",
        )
        self.facilities.update(
            {
                "river_bend": river_bend,
                "summit_ridge": summit_ridge,
            }
        )

        rb_aquatics = self._upsert(
            Department,
            {"name": "River Bend Aquatics"},
            {
                "description": "Waterfront staff and programming.",
                "facility": river_bend,
                "abbreviation": "RBA",
            },
            label="River Bend Aquatics",
        )
        rb_skills = self._upsert(
            Department,
            {"name": "River Bend Outdoor Skills"},
            {
                "description": "Trailcraft, survival, and pioneering.",
                "facility": river_bend,
                "abbreviation": "RBOS",
            },
            label="River Bend Outdoor Skills",
        )
        summit_lab = self._upsert(
            Department,
            {"name": "Summit Ridge STEM Lab"},
            {
                "description": "Leadership lab for STEM-focused courses.",
                "facility": summit_ridge,
                "abbreviation": "SRSL",
            },
            label="Summit Ridge STEM Lab",
        )
        self.departments.update(
            {
                "rb_aquatics": rb_aquatics,
                "rb_skills": rb_skills,
                "summit_lab": summit_lab,
            }
        )

    def _create_quarters(self):
        cascade = self.orgs["cascade"]
        cabin_type = self._upsert(
            QuartersType,
            {"name": "Cabin Village"},
            {
                "description": "Premium cabins used for faculty and leaders.",
                "organization": cascade,
            },
            label="Cabin Village",
        )
        tent_type = self._upsert(
            QuartersType,
            {"name": "Tent Meadow"},
            {
                "description": "Canvas wall-tents near the training ranges.",
                "organization": cascade,
            },
            label="Tent Meadow",
        )
        faction_type = self._upsert(
            QuartersType,
            {"name": "Faction Quarters"},
            {
                "description": "Reserved quarters for faction cohorts.",
                "organization": cascade,
                "slug": "faction",
            },
            label="Faction Quarters",
        )
        leader_type = self._upsert(
            QuartersType,
            {"name": "Leader Quarters"},
            {
                "description": "Reserved for faction leaders.",
                "organization": cascade,
                "slug": "leader",
            },
            label="Leader Quarters",
        )
        attendee_type = self._upsert(
            QuartersType,
            {"name": "Attendee Quarters"},
            {
                "description": "Reserved for attendees.",
                "organization": cascade,
                "slug": "attendee",
            },
            label="Attendee Quarters",
        )
        faculty_type = self._upsert(
            QuartersType,
            {"name": "Faculty Quarters"},
            {
                "description": "Reserved for faculty assignments.",
                "organization": cascade,
                "slug": "faculty",
            },
            label="Faculty Quarters",
        )
        self.quarters_types.update(
            {
                "cabin": cabin_type,
                "tent": tent_type,
                "faction": faction_type,
                "leader": leader_type,
                "attendee": attendee_type,
                "faculty": faculty_type,
            }
        )

        river_bend = self.facilities["river_bend"]
        summit_ridge = self.facilities["summit_ridge"]

        pinecone = self._upsert(
            Quarters,
            {"name": "Pinecone Cabins"},
            {
                "description": "Cabin ring closest to the medical lodge.",
                "capacity": 40,
                "type": cabin_type,
                "facility": river_bend,
            },
            label="Pinecone Cabins",
        )
        pinecone_faction = self._upsert(
            Quarters,
            {"name": "Pinecone Cabins - Faction"},
            {
                "description": "Faction-dedicated block of Pinecone Cabins.",
                "capacity": 24,
                "type": faction_type,
                "facility": river_bend,
            },
            label="Pinecone Cabins - Faction",
        )
        riverside = self._upsert(
            Quarters,
            {"name": "Riverside Tents"},
            {
                "description": "Tents along the river bend boardwalk.",
                "capacity": 60,
                "type": tent_type,
                "facility": river_bend,
            },
            label="Riverside Tents",
        )
        summit_lodge = self._upsert(
            Quarters,
            {"name": "Summit Lodge"},
            {
                "description": "Small lodge for leadership cohorts.",
                "capacity": 30,
                "type": cabin_type,
                "facility": summit_ridge,
            },
            label="Summit Lodge",
        )
        summit_lodge_faction = self._upsert(
            Quarters,
            {"name": "Summit Lodge - Faction"},
            {
                "description": "Reserved wing of Summit Lodge for faction cohorts.",
                "capacity": 20,
                "type": faction_type,
                "facility": summit_ridge,
            },
            label="Summit Lodge - Faction",
        )
        leader_quarters = self._upsert(
            Quarters,
            {"name": "Leader Cabins"},
            {
                "description": "Leader-only cabins near administration.",
                "capacity": 20,
                "type": leader_type,
                "facility": river_bend,
            },
            label="Leader Cabins",
        )
        attendee_quarters = self._upsert(
            Quarters,
            {"name": "Attendee Tents"},
            {
                "description": "Standard attendee tent sites.",
                "capacity": 80,
                "type": attendee_type,
                "facility": river_bend,
            },
            label="Attendee Tents",
        )
        faculty_quarters = self._upsert(
            Quarters,
            {"name": "Faculty Lodge"},
            {
                "description": "Faculty lodging with workspace.",
                "capacity": 25,
                "type": faculty_type,
                "facility": summit_ridge,
            },
            label="Faculty Lodge",
        )
        self.quarters.update(
            {
                "pinecone": pinecone,
                "pinecone_faction": pinecone_faction,
                "riverside": riverside,
                "summit_lodge": summit_lodge,
                "summit_lodge_faction": summit_lodge_faction,
                "leader_quarters": leader_quarters,
                "attendee_quarters": attendee_quarters,
                "faculty_quarters": faculty_quarters,
            }
        )

    def _create_factions(self):
        cascade = self.orgs["cascade"]
        eagle = self._upsert(
            Faction,
            {"name": "Eagle Patrol"},
            {
                "slug": "eagle-patrol",
                "description": "High-performing patrol specializing in outdoor leadership.",
                "abbreviation": "EP",
                "organization": cascade,
                "parent": None,
            },
            label="Eagle Patrol",
        )
        eagle_foxes = self._upsert(
            Faction,
            {"name": "Eagle Patrol - Foxes"},
            {
                "slug": "eagle-patrol-foxes",
                "description": "Foxes squad for first-years.",
                "abbreviation": "EPF",
                "organization": cascade,
                "parent": eagle,
            },
            label="Eagle Patrol Foxes",
        )
        aurora = self._upsert(
            Faction,
            {"name": "Aurora Crew"},
            {
                "slug": "aurora-crew",
                "description": "Co-ed crew focused on STEM and expedition planning.",
                "abbreviation": "AC",
                "organization": cascade,
                "parent": None,
            },
            label="Aurora Crew",
        )
        aurora_voyagers = self._upsert(
            Faction,
            {"name": "Aurora Crew - Voyagers"},
            {
                "slug": "aurora-crew-voyagers",
                "description": "Voyagers sub-crew specializing in logistics.",
                "abbreviation": "ACV",
                "organization": cascade,
                "parent": aurora,
            },
            label="Aurora Crew Voyagers",
        )
        self.factions.update(
            {
                "eagle": eagle,
                "eagle_foxes": eagle_foxes,
                "aurora": aurora,
                "aurora_voyagers": aurora_voyagers,
            }
        )

    def _create_courses(self):
        medical = self._upsert(
            Requirement,
            {"name": "General Medical Release"},
            {"description": "Signed release kept on file for high-adventure activities."},
            label="General Medical Release",
        )
        navigation = self._upsert(
            Requirement,
            {"name": "Compass Fundamentals"},
            {"description": "Evidence of compass and map basics."},
            label="Compass Fundamentals",
        )
        interview = self._upsert(
            Requirement,
            {"name": "Team Leadership Interview"},
            {"description": "Short interview ensuring readiness for leadership cohorts."},
            label="Team Leadership Interview",
        )
        self.requirements.update(
            {"medical": medical, "navigation": navigation, "interview": interview}
        )

        wfa = self._upsert(
            Course,
            {"name": "Wilderness First Aid"},
            {
                "description": "Scenario-driven medical training for remote settings.",
                "duration_in_days": 3,
                "popularity": 95,
                "average_rating": 4.8,
            },
            label="Wilderness First Aid",
        )
        wfa.requirements.set([medical])
        wfa.tags.set(["medical", "safety"])

        nav = self._upsert(
            Course,
            {"name": "Backcountry Navigation"},
            {
                "description": "Hands-on orienteering intensive using live scenarios.",
                "duration_in_days": 2,
                "popularity": 88,
                "average_rating": 4.6,
            },
            label="Backcountry Navigation",
        )
        nav.requirements.set([navigation])
        nav.tags.set(["navigation", "outdoor-skills"])

        leader = self._upsert(
            Course,
            {"name": "Emerging Leader Workshop"},
            {
                "description": "Facilitated cohort exploring service leadership patterns.",
                "duration_in_days": 4,
                "popularity": 91,
                "average_rating": 4.7,
            },
            label="Emerging Leader Workshop",
        )
        leader.requirements.set([interview])
        leader.tags.set(["leadership", "team"])

        self.courses.update({"wfa": wfa, "nav": nav, "leader": leader})

    def _create_organization_enrollments(self):
        cascade = self.orgs["cascade"]
        summer = self._upsert(
            OrganizationEnrollment,
            {"name": "2025 Summer Adventure"},
            {
                "description": "Primary summer enrollment window for Cascades.",
                "start": date(2025, 6, 1),
                "end": date(2025, 8, 31),
                "organization": cascade,
            },
            label="2025 Summer Adventure",
        )
        self.organization_enrollments["summer"] = summer

        for key, course in self.courses.items():
            org_course = self._upsert(
                OrganizationCourse,
                {"name": f"{course.name} - Summer 2025"},
                {
                    "description": f"{course.description} (Summer Cohort)",
                    "course": course,
                    "organization_enrollment": summer,
                },
                label=f"{course.name} - Summer 2025",
            )
            self.organization_courses[key] = org_course

    def _create_facility_enrollments(self):
        summer = self.organization_enrollments["summer"]
        river_bend = self.facilities["river_bend"]
        summit_ridge = self.facilities["summit_ridge"]

        rb_session = self._upsert(
            FacilityEnrollment,
            {"name": "River Bend Session 1"},
            {
                "description": "First early-summer session at River Bend.",
                "start": date(2025, 6, 1),
                "end": date(2025, 6, 28),
                "organization_enrollment": summer,
                "facility": river_bend,
                "status": "active",
            },
            label="River Bend Session 1",
        )
        summit_session = self._upsert(
            FacilityEnrollment,
            {"name": "Summit Ridge Intensive"},
            {
                "description": "Leadership-intensive block at Summit Ridge.",
                "start": date(2025, 7, 5),
                "end": date(2025, 8, 2),
                "organization_enrollment": summer,
                "facility": summit_ridge,
                "status": "active",
            },
            label="Summit Ridge Intensive",
        )
        self.facility_enrollments.update(
            {"river_bend": rb_session, "summit_ridge": summit_session}
        )

        week_definitions = [
            ("river_w1", rb_session, "River Bend Week 1", date(2025, 6, 2), date(2025, 6, 8)),
            ("river_w2", rb_session, "River Bend Week 2", date(2025, 6, 9), date(2025, 6, 15)),
            ("summit_w1", summit_session, "Summit Ridge Week 1", date(2025, 7, 7), date(2025, 7, 13)),
        ]
        for key, enrollment, name, start_day, end_day in week_definitions:
            week = self._upsert(
                Week,
                {"name": name},
                {
                    "description": f"{name} calendar block.",
                    "facility_enrollment": enrollment,
                    "start": start_day,
                    "end": end_day,
                },
                label=name,
            )
            self.weeks[key] = week

        period_definitions = [
            ("river_w1_morning", self.weeks["river_w1"], "RB Week 1 Morning", time(9, 0), time(12, 0)),
            ("river_w1_afternoon", self.weeks["river_w1"], "RB Week 1 Afternoon", time(13, 0), time(16, 0)),
            ("river_w2_morning", self.weeks["river_w2"], "RB Week 2 Morning", time(9, 0), time(12, 0)),
            ("river_w2_afternoon", self.weeks["river_w2"], "RB Week 2 Afternoon", time(13, 0), time(16, 0)),
            ("summit_w1_morning", self.weeks["summit_w1"], "Summit Week 1 Morning", time(8, 30), time(11, 30)),
            ("summit_w1_afternoon", self.weeks["summit_w1"], "Summit Week 1 Afternoon", time(13, 30), time(16, 30)),
        ]
        for key, week, name, start_time, end_time in period_definitions:
            period = self._upsert(
                Period,
                {"name": name},
                {
                    "description": f"{name} instruction block.",
                    "week": week,
                    "start": start_time,
                    "end": end_time,
                },
                label=name,
            )
            self.periods[key] = period

    def _create_facility_classes(self):
        rb_session = self.facility_enrollments["river_bend"]
        summit_session = self.facility_enrollments["summit_ridge"]
        summer = self.organization_enrollments["summer"]

        rb_wfa = self._upsert(
            FacilityClass,
            {"name": "River Bend Wilderness First Aid"},
            {
                "description": "All River Bend medical staff and faculty train together.",
                "organization_course": self.organization_courses["wfa"],
                "facility_enrollment": rb_session,
                "max_enrollment": 24,
            },
            label="River Bend Wilderness First Aid",
        )
        rb_nav = self._upsert(
            FacilityClass,
            {"name": "River Bend Navigation Lab"},
            {
                "description": "Daily backcountry navigation scenarios.",
                "organization_course": self.organization_courses["nav"],
                "facility_enrollment": rb_session,
                "max_enrollment": 28,
            },
            label="River Bend Navigation Lab",
        )
        summit_leader = self._upsert(
            FacilityClass,
            {"name": "Summit Ridge Leadership Cohort"},
            {
                "description": "Residential leadership cohort with project mentors.",
                "organization_course": self.organization_courses["leader"],
                "facility_enrollment": summit_session,
                "max_enrollment": 18,
            },
            label="Summit Ridge Leadership Cohort",
        )
        self.facility_classes.update(
            {
                "rb_wfa": rb_wfa,
                "rb_nav": rb_nav,
                "summit_leader": summit_leader,
            }
        )

        rb_session.facility_classes.add(rb_wfa, rb_nav)
        summit_session.facility_classes.add(summit_leader)

        class_enrollment_defs = [
            (
                "rb_wfa_week1_morning",
                rb_wfa,
                self.periods["river_w1_morning"],
                self.departments["rb_aquatics"],
                18,
            ),
            (
                "rb_nav_week2_afternoon",
                rb_nav,
                self.periods["river_w2_afternoon"],
                self.departments["rb_skills"],
                24,
            ),
            (
                "summit_leader_morning",
                summit_leader,
                self.periods["summit_w1_morning"],
                self.departments["summit_lab"],
                16,
            ),
        ]

        for key, facility_class, period, department, max_size in class_enrollment_defs:
            enrollment = self._upsert(
                FacilityClassEnrollment,
                {"name": f"{facility_class.name} - {period.name}"},
                {
                    "description": f"{facility_class.name} during {period.name}.",
                    "facility_class": facility_class,
                    "period": period,
                    "department": department,
                    "organization_enrollment": summer,
                    "max_enrollment": max_size,
                },
                label=f"{facility_class.name} - {period.name}",
            )
            self.class_enrollments[key] = enrollment

    def _create_users_and_profiles(self):
        cascade = self.orgs["cascade"]
        river_bend = self.facilities["river_bend"]
        summit_ridge = self.facilities["summit_ridge"]
        eagle = self.factions["eagle"]
        aurora = self.factions["aurora"]

        with muted_profile_signals():
            self.users["admin"] = self._create_user(
                username="campfire.admin",
                email="admin@campfire.local",
                first_name="Ada",
                last_name="Admin",
                user_type=User.UserType.ADMIN,
                is_staff=True,
                is_superuser=True,
            )
            self.users["river_faculty"] = self._create_user(
                username="donna.faculty",
                email="donna.faculty@campfire.local",
                first_name="Donna",
                last_name="Rivera",
                user_type=User.UserType.FACULTY,
            )
            self.users["summit_faculty"] = self._create_user(
                username="mason.faculty",
                email="mason.faculty@campfire.local",
                first_name="Mason",
                last_name="Greene",
                user_type=User.UserType.FACULTY,
            )
            self.users["eagle_leader"] = self._create_user(
                username="leo.leader",
                email="leo.leader@campfire.local",
                first_name="Leo",
                last_name="Castor",
                user_type=User.UserType.LEADER,
            )
            self.users["aurora_leader"] = self._create_user(
                username="sara.leader",
                email="sara.leader@campfire.local",
                first_name="Sara",
                last_name="Nguyen",
                user_type=User.UserType.LEADER,
            )
            self.users["attendee_amy"] = self._create_user(
                username="amy.attendee",
                email="amy.attendee@campfire.local",
                first_name="Amy",
                last_name="Lopez",
                user_type=User.UserType.ATTENDEE,
            )
            self.users["attendee_riley"] = self._create_user(
                username="riley.attendee",
                email="riley.attendee@campfire.local",
                first_name="Riley",
                last_name="Chen",
                user_type=User.UserType.ATTENDEE,
            )

        self.faculty_profiles["river_faculty"], _ = FacultyProfile.objects.update_or_create(
            user=self.users["river_faculty"],
            defaults={
                "organization": cascade,
                "facility": river_bend,
                "role": FacultyProfile.FacultyRole.ADMIN,
            },
        )
        self.faculty_profiles["summit_faculty"], _ = FacultyProfile.objects.update_or_create(
            user=self.users["summit_faculty"],
            defaults={
                "organization": cascade,
                "facility": summit_ridge,
                "role": FacultyProfile.FacultyRole.DEPARTMENT_ADMIN,
            },
        )

        self.leader_profiles["eagle"], _ = LeaderProfile.objects.update_or_create(
            user=self.users["eagle_leader"],
            defaults={
                "organization": cascade,
                "faction": eagle,
                "is_admin": True,
            },
        )
        self.leader_profiles["aurora"], _ = LeaderProfile.objects.update_or_create(
            user=self.users["aurora_leader"],
            defaults={
                "organization": cascade,
                "faction": aurora,
                "is_admin": False,
            },
        )

        self.attendee_profiles["amy"], _ = AttendeeProfile.objects.update_or_create(
            user=self.users["attendee_amy"],
            defaults={
                "organization": cascade,
                "faction": self.factions["eagle_foxes"],
            },
        )
        self.attendee_profiles["riley"], _ = AttendeeProfile.objects.update_or_create(
            user=self.users["attendee_riley"],
            defaults={
                "organization": cascade,
                "faction": self.factions["aurora_voyagers"],
            },
        )

    def _create_user(self, username, email, first_name, last_name, user_type, is_staff=False, is_superuser=False):
        user, _ = User.objects.get_or_create(username=username, defaults={"user_type": user_type})
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.user_type = user_type
        user.is_staff = is_staff or is_superuser
        user.is_superuser = is_superuser
        user.is_admin = user_type == User.UserType.ADMIN or is_superuser
        user.is_active = True
        user.is_new_user = False
        user.set_password("testpass123")
        user.save()
        self._log(f"  - User {username} ensured")
        return user

    def _create_faction_enrollments(self):
        rb_session = self.facility_enrollments["river_bend"]
        summit_session = self.facility_enrollments["summit_ridge"]
        pinecone = self.quarters.get("pinecone_faction") or self.quarters["pinecone"]
        summit_lodge = (
            self.quarters.get("summit_lodge_faction") or self.quarters["summit_lodge"]
        )

        eagle_enrollment = self._upsert(
            FactionEnrollment,
            {"name": "Eagle Patrol Week 1"},
            {
                "description": "Eagle Patrol assigned to River Bend Week 1.",
                "facility_enrollment": rb_session,
                "start": rb_session.start,
                "end": rb_session.start + timedelta(days=6),
                "faction": self.factions["eagle"],
                "week": self.weeks["river_w1"],
                "quarters": pinecone,
            },
            label="Eagle Patrol Week 1",
        )
        aurora_enrollment = self._upsert(
            FactionEnrollment,
            {"name": "Aurora Crew Summit Cohort"},
            {
                "description": "Aurora Crew cohort at Summit Ridge.",
                "facility_enrollment": summit_session,
                "start": summit_session.start,
                "end": summit_session.start + timedelta(days=6),
                "faction": self.factions["aurora"],
                "week": self.weeks["summit_w1"],
                "quarters": summit_lodge,
            },
            label="Aurora Crew Summit Cohort",
        )
        self.faction_enrollments.update(
            {"eagle": eagle_enrollment, "aurora": aurora_enrollment}
        )

    def _create_person_enrollments(self):
        pinecone = self.quarters["pinecone"]
        riverside = self.quarters["riverside"]
        summit_lodge = self.quarters["summit_lodge"]
        rb_session = self.facility_enrollments["river_bend"]
        leader_eagle = self.leader_profiles["eagle"]
        leader_aurora = self.leader_profiles["aurora"]
        attendee_amy = self.attendee_profiles["amy"]
        attendee_riley = self.attendee_profiles["riley"]

        faculty_enrollment = self._upsert(
            FacultyEnrollmentRecord,
            {"name": "Donna Rivera Faculty Assignment"},
            {
                "description": "Primary medical instructor for River Bend.",
                "faculty": self.faculty_profiles["river_faculty"],
                "facility_enrollment": rb_session,
                "quarters": pinecone,
                "role": "Medical Lead",
            },
            label="Donna Rivera Faculty Assignment",
        )
        self.faculty_enrollments["river"] = faculty_enrollment

        leader_eagle_enrollment = self._upsert(
            LeaderEnrollmentRecord,
            {"name": "Leo Castor Week 1"},
            {
                "description": "Lead advisor for Eagle Patrol.",
                "leader": leader_eagle,
                "faction_enrollment": self.faction_enrollments["eagle"],
                "quarters": pinecone,
                "role": "Unit Leader",
            },
            label="Leo Castor Week 1",
        )
        self.leader_enrollments["eagle"] = leader_eagle_enrollment

        leader_aurora_enrollment = self._upsert(
            LeaderEnrollmentRecord,
            {"name": "Sara Nguyen Summit"},
            {
                "description": "Aurora Crew mentor at Summit Ridge.",
                "leader": leader_aurora,
                "faction_enrollment": self.faction_enrollments["aurora"],
                "quarters": summit_lodge,
                "role": "Cohort Guide",
            },
            label="Sara Nguyen Summit",
        )
        self.leader_enrollments["aurora"] = leader_aurora_enrollment

        attendee_amy_enrollment = self._upsert(
            AttendeeEnrollmentRecord,
            {"name": "Amy Lopez Navigation Track"},
            {
                "description": "Assigned to navigation lab and Eagle Patrol.",
                "attendee": attendee_amy,
                "faction_enrollment": self.faction_enrollments["eagle"],
                "quarters": riverside,
                "role": "Patrol Scribe",
            },
            label="Amy Lopez Navigation Track",
        )
        attendee_riley_enrollment = self._upsert(
            AttendeeEnrollmentRecord,
            {"name": "Riley Chen Summit Cohort"},
            {
                "description": "STEM leadership resident.",
                "attendee": attendee_riley,
                "faction_enrollment": self.faction_enrollments["aurora"],
                "quarters": summit_lodge,
                "role": "Project Lead",
            },
            label="Riley Chen Summit Cohort",
        )
        self.attendee_enrollments.update(
            {"amy": attendee_amy_enrollment, "riley": attendee_riley_enrollment}
        )

        self._ensure_active_enrollments()
        self._ensure_generic_enrollments()

    def _ensure_active_enrollments(self):
        mappings = [
            (
                self.users["river_faculty"],
                {"faculty_enrollment": self.faculty_enrollments["river"]},
            ),
            (
                self.users["eagle_leader"],
                {"leader_enrollment": self.leader_enrollments["eagle"]},
            ),
            (
                self.users["aurora_leader"],
                {"leader_enrollment": self.leader_enrollments["aurora"]},
            ),
            (
                self.users["attendee_amy"],
                {"attendee_enrollment": self.attendee_enrollments["amy"]},
            ),
            (
                self.users["attendee_riley"],
                {"attendee_enrollment": self.attendee_enrollments["riley"]},
            ),
        ]
        for user, fields in mappings:
            defaults = {
                "attendee_enrollment": None,
                "leader_enrollment": None,
                "faction_enrollment": None,
                "faculty_enrollment": None,
                "facility_enrollment": None,
            }
            defaults.update(fields)
            ActiveEnrollment.objects.update_or_create(user=user, defaults=defaults)
            self._log(f"  - Active enrollment linked for {user.username}")

    def _ensure_generic_enrollments(self):
        records = [
            (self.users["river_faculty"], self.faculty_enrollments["river"]),
            (self.users["eagle_leader"], self.leader_enrollments["eagle"]),
            (self.users["aurora_leader"], self.leader_enrollments["aurora"]),
            (self.users["attendee_amy"], self.attendee_enrollments["amy"]),
            (self.users["attendee_riley"], self.attendee_enrollments["riley"]),
        ]

        for user, enrollment in records:
            content_type = ContentType.objects.get_for_model(enrollment)
            GenericEnrollment.objects.update_or_create(
                user=user,
                enrollment_type=content_type,
                enrollment_id=enrollment.pk,
                defaults={},
            )
            self._log(f"  - Enrollment record synced for {user.username}")
