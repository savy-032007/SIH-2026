"""Institution portal router delivering the full backend for the institution dashboard,
student list, student add/edit, validation results, and settings.
"""

from __future__ import annotations

import re
import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.institution import (
    CategoryDistributionItem,
    ChangePasswordRequest,
    CreateInstitutionalUserRequest,
    CreateStudentRequest,
    DashboardResponse,
    DashboardStats,
    DonutLegendItem,
    EnrolmentTrendPoint,
    FlaggedRecordItem,
    InstitutionalUser,
    InstitutionProfile,
    IssueBreakdownItem,
    NotificationPreferences,
    RecentActivityItem,
    SecurityOverview,
    StudentListItem,
    StudentListResponse,
    UpdateInstitutionProfileRequest,
    UploadBatchItem,
    UploadDataResponse,
    ValidationDonutData,
    ValidationResultsResponse,
    ValidationStats,
    VerifyApaarRequest,
    VerifyApaarResponse,
)
from app.integrations.digilocker import DigiLockerProvider
from app.integrations.factory import get_digilocker

router = APIRouter(prefix="/institution", tags=["institution"])

# --------------------------------------------------------------------------- #
# State Storage (Initialized with the exact records from UI mockup)
# --------------------------------------------------------------------------- #

_PROFILE = InstitutionProfile(
    institution_name="XYZ College of Engineering",
    institution_id="INST001",
    aicte_approval_no="1-12345678901",
    address="123 College Road, Pune, Maharashtra, India - 411001",
    contact_email="admin@xyzcollege.ac.in",
    contact_number="+91 9876543210",
    academic_year="2025",
    approved_intake=600,
    logo_url="/aicte-logo.png",
)

_INITIAL_STUDENTS: list[StudentListItem] = [
    StudentListItem(
        id="std-001",
        row_num=1,
        name="Aarav Sharma",
        apaar_id="123456789012",
        course="B.Tech CSE",
        year="2025",
        category="General",
        status="Valid",
        student_id_college="MT001",
        gender="Male",
        dob="2005-06-15",
    ),
    StudentListItem(
        id="std-002",
        row_num=2,
        name="Neha Kapoor",
        apaar_id="987654321098",
        course="B.Tech ECE",
        year="2025",
        category="OBC",
        status="Valid",
        student_id_college="MT002",
        gender="Female",
        dob="2005-08-22",
    ),
    StudentListItem(
        id="std-003",
        row_num=3,
        name="Rohan Mehta",
        apaar_id="111222333444",
        course="B.Tech AIML",
        year="2025",
        category="General",
        status="Needs Correction",
        student_id_college="MT003",
        gender="Male",
        dob="2005-03-10",
    ),
    StudentListItem(
        id="std-004",
        row_num=4,
        name="Sneha Patel",
        apaar_id="555666777888",
        course="B.Tech ME",
        year="2025",
        category="SC",
        status="Valid",
        student_id_college="MT004",
        gender="Female",
        dob="2005-11-05",
    ),
    StudentListItem(
        id="std-005",
        row_num=5,
        name="Karan Singh",
        apaar_id="999888777666",
        course="B.Tech CE",
        year="2025",
        category="OBC",
        status="Flagged",
        student_id_college="MT005",
        gender="Male",
        dob="2004-12-18",
    ),
    StudentListItem(
        id="std-006",
        row_num=6,
        name="Isha Verma",
        apaar_id="222333444555",
        course="B.Pharm",
        year="2025",
        category="General",
        status="Valid",
        student_id_college="MT006",
        gender="Female",
        dob="2005-04-30",
    ),
    StudentListItem(
        id="std-007",
        row_num=7,
        name="Aditya Rao",
        apaar_id="333444555666",
        course="MBA",
        year="2025",
        category="NRI",
        status="Valid",
        student_id_college="MT007",
        gender="Male",
        dob="2003-09-14",
    ),
    StudentListItem(
        id="std-008",
        row_num=8,
        name="Pooja Nair",
        apaar_id="444555666777",
        course="B.Tech CSE",
        year="2025",
        category="OCI",
        status="Valid",
        student_id_college="MT008",
        gender="Female",
        dob="2005-01-25",
    ),
]

_STUDENTS_STORE: list[StudentListItem] = list(_INITIAL_STUDENTS)

_RECENT_ACTIVITIES: list[RecentActivityItem] = [
    RecentActivityItem(
        id=1,
        activity="Student Added",
        details="Aarav Sharma (APAAR ID: 123456789012)",
        datetime="25 Apr 2025, 10:45 AM",
        type="success",
    ),
    RecentActivityItem(
        id=2,
        activity="Student Updated",
        details="Neha Kapoor (Course: B.Tech CSE)",
        datetime="25 Apr 2025, 09:30 AM",
        type="info",
    ),
    RecentActivityItem(
        id=3,
        activity="Validation Alert",
        details="Duplicate APAAR ID detected",
        datetime="24 Apr 2025, 05:20 PM",
        type="alert",
    ),
]

_FLAGGED_RECORDS: list[FlaggedRecordItem] = [
    FlaggedRecordItem(
        id="flg-1",
        row_num=1,
        student_name="Rohan Mehta",
        apaar_id="111222333444",
        issue="Missing APAAR ID",
        status="Needs Correction",
        details="APAAR verification pending student consent or missing in registry.",
    ),
    FlaggedRecordItem(
        id="flg-2",
        row_num=2,
        student_name="Karan Singh",
        apaar_id="999888777666",
        issue="Duplicate APAAR ID",
        status="Flagged",
        details="APAAR ID already associated with active record at another institution.",
    ),
    FlaggedRecordItem(
        id="flg-3",
        row_num=3,
        student_name="Priya Desai",
        apaar_id="123456789012",
        issue="Excess Enrolment",
        status="Flagged",
        details="Course approved intake limit breached for academic year 2025.",
    ),
    FlaggedRecordItem(
        id="flg-4",
        row_num=4,
        student_name="Amit Kumar",
        apaar_id="777888999000",
        issue="Inconsistent Course Data",
        status="Needs Correction",
        details="Supernumerary category claimed without valid foreign qualification board.",
    ),
]


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@router.get("/dashboard", response_model=DashboardResponse, summary="Institution Dashboard Overview")
def get_dashboard() -> DashboardResponse:
    """Return KPI cards, enrolment trend, category distribution, and recent activities."""
    total_students = 585 + len(_STUDENTS_STORE) - len(_INITIAL_STUDENTS)
    actual_enrolment = 570 + len(_STUDENTS_STORE) - len(_INITIAL_STUDENTS)
    remaining_seats = max(0, 600 - actual_enrolment)

    stats = DashboardStats(
        approved_intake=600,
        actual_enrolment=actual_enrolment,
        remaining_seats=remaining_seats,
        total_students=total_students,
    )

    enrolment_trend = [
        EnrolmentTrendPoint(year="2022", actual=450, approved=600),
        EnrolmentTrendPoint(year="2023", actual=485, approved=600),
        EnrolmentTrendPoint(year="2024", actual=520, approved=600),
        EnrolmentTrendPoint(year="2025", actual=565, approved=600),
        EnrolmentTrendPoint(year="2026", actual=actual_enrolment, approved=600),
    ]

    category_distribution = [
        CategoryDistributionItem(category="General", count=320, percentage=54.7, color="#3B82F6"),
        CategoryDistributionItem(category="OBC", count=120, percentage=20.5, color="#F59E0B"),
        CategoryDistributionItem(category="SC", count=60, percentage=10.3, color="#10B981"),
        CategoryDistributionItem(category="ST", count=35, percentage=6.0, color="#EF4444"),
        CategoryDistributionItem(category="NRI", count=25, percentage=4.3, color="#8B5CF6"),
        CategoryDistributionItem(category="OCI", count=15, percentage=2.6, color="#EC4899"),
        CategoryDistributionItem(category="Foreign National", count=10, percentage=1.7, color="#06B6D4"),
    ]

    return DashboardResponse(
        institution_name=_PROFILE.institution_name,
        institution_id=_PROFILE.institution_id,
        aicte_approval=_PROFILE.aicte_approval_no,
        academic_year=_PROFILE.academic_year,
        admin_name="Priya Verma",
        admin_role="Institution Admin",
        stats=stats,
        enrolment_trend=enrolment_trend,
        category_distribution=category_distribution,
        recent_activities=_RECENT_ACTIVITIES,
    )


@router.get("/students", response_model=StudentListResponse, summary="List Student Records")
def list_students(
    search: Annotated[str | None, Query(description="Search by name, APAAR ID, or student ID")] = None,
    course: Annotated[str | None, Query(description="Filter by course")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    status: Annotated[str | None, Query(description="Filter by status (Valid, Needs Correction, Flagged)")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 8,
) -> StudentListResponse:
    """Paginated student list with search and filters matching Screen 2."""
    filtered = _STUDENTS_STORE

    if search:
        q = search.strip().lower()
        filtered = [
            s for s in filtered
            if q in s.name.lower()
            or q in s.apaar_id.lower()
            or (s.student_id_college and q in s.student_id_college.lower())
        ]

    if course and course not in ("All Courses", "all", ""):
        filtered = [s for s in filtered if s.course.lower() == course.lower()]

    if category and category not in ("All Categories", "all", ""):
        filtered = [s for s in filtered if s.category.lower() == category.lower()]

    if status and status not in ("All Status", "all", ""):
        filtered = [s for s in filtered if s.status.lower() == status.lower()]

    total = len(filtered)
    # Virtual total matching the 585 indicator on UI if no restrictive filter
    display_total = 585 if not search and not course and not category and not status else total

    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    total_pages = max(1, (display_total + page_size - 1) // page_size)

    return StudentListResponse(
        students=paginated,
        total=display_total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/students/{student_id}", response_model=StudentListItem, summary="Get Single Student")
def get_student(student_id: str) -> StudentListItem:
    for s in _STUDENTS_STORE:
        if s.id == student_id:
            return s
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")


@router.post("/students", response_model=StudentListItem, status_code=status.HTTP_201_CREATED, summary="Add New Student")
def add_student(payload: CreateStudentRequest) -> StudentListItem:
    """Add a new student record (Screen 3: Add Student Form)."""
    # Validation of 12-digit APAAR ID
    clean_apaar = payload.apaar_id.replace(" ", "").replace("-", "")
    if not re.match(r"^\d{12}$", clean_apaar):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="APAAR ID must be exactly 12 numeric digits.",
        )

    # Status derivation: Check if APAAR has duplicate or category anomaly
    derived_status = "Valid"
    if clean_apaar.startswith("999") or clean_apaar.startswith("000"):
        derived_status = "Flagged"
    elif payload.foreign_national.lower() == "yes" and not payload.remarks:
        derived_status = "Needs Correction"

    new_id = f"std-{uuid.uuid4().hex[:6]}"
    new_item = StudentListItem(
        id=new_id,
        row_num=len(_STUDENTS_STORE) + 1,
        name=payload.name.strip(),
        apaar_id=clean_apaar,
        course=payload.course.strip(),
        year=payload.admission_year.strip(),
        category="NRI" if payload.nri_category.lower() == "yes" else (
            "OCI" if payload.oci_status.lower() == "yes" else (
                "FN" if payload.foreign_national.lower() == "yes" else "General"
            )
        ),
        status=derived_status,
        student_id_college=payload.student_id_college.strip(),
        gender=payload.gender,
        dob=payload.dob,
    )

    _STUDENTS_STORE.insert(0, new_item)

    # Re-index row numbers
    for idx, s in enumerate(_STUDENTS_STORE, start=1):
        s.row_num = idx

    # Add to recent activities
    _RECENT_ACTIVITIES.insert(
        0,
        RecentActivityItem(
            id=len(_RECENT_ACTIVITIES) + 1,
            activity="Student Added",
            details=f"{payload.name.strip()} (APAAR ID: {clean_apaar})",
            datetime="Just now",
            type="success",
        ),
    )

    return new_item


@router.put("/students/{student_id}", response_model=StudentListItem, summary="Update Student")
def update_student(student_id: str, payload: CreateStudentRequest) -> StudentListItem:
    for s in _STUDENTS_STORE:
        if s.id == student_id:
            s.name = payload.name.strip()
            s.apaar_id = payload.apaar_id.strip()
            s.course = payload.course.strip()
            s.year = payload.admission_year.strip()
            s.student_id_college = payload.student_id_college.strip()
            s.gender = payload.gender
            s.dob = payload.dob

            _RECENT_ACTIVITIES.insert(
                0,
                RecentActivityItem(
                    id=len(_RECENT_ACTIVITIES) + 1,
                    activity="Student Updated",
                    details=f"{s.name} (Course: {s.course})",
                    datetime="Just now",
                    type="info",
                ),
            )
            return s

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Student")
def delete_student(student_id: str) -> None:
    global _STUDENTS_STORE
    _STUDENTS_STORE = [s for s in _STUDENTS_STORE if s.id != student_id]
    for idx, s in enumerate(_STUDENTS_STORE, start=1):
        s.row_num = idx


@router.post("/students/verify-apaar", response_model=VerifyApaarResponse, summary="Verify APAAR ID")
def verify_apaar(
    payload: VerifyApaarRequest,
    digilocker: DigiLockerProvider = Depends(get_digilocker),
) -> VerifyApaarResponse:
    """Verifies APAAR ID against the active DigiLocker / API Setu ABC ID card adapter."""
    apaar_clean = payload.apaar_id.replace(" ", "").replace("-", "")

    if not re.match(r"^\d{12}$", apaar_clean):
        return VerifyApaarResponse(
            apaar_id=apaar_clean,
            valid=False,
            exists=False,
            status="INVALID_FORMAT",
            message="APAAR ID must be exactly 12 numeric digits.",
        )

    student_name = payload.name or payload.student_name

    # Query the DigiLocker adapter (API Setu Sandbox or Mock)
    doc = digilocker.verify_apaar(
        apaar_id=apaar_clean,
        name=student_name,
        dob=payload.dob,
        gender=payload.gender,
        admission_year=payload.admission_year,
        mobile=payload.mobile,
        email=payload.email,
    )

    # Mask name if provided or generate realistic masked name
    masked = None
    if student_name:
        parts = student_name.split()
        masked = " ".join([p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts])
    else:
        masked = "A**** S*****"

    hash_preview = f" [Hash: {doc.sha256[:8]}]" if doc.sha256 else ""
    return VerifyApaarResponse(
        apaar_id=apaar_clean,
        valid=True,
        exists=True,
        masked_name=masked,
        status="ACTIVE",
        message=f"APAAR ID verified via {doc.issuer}{hash_preview}.",
        doc_type=doc.doc_type,
        issuer=doc.issuer,
        sha256=doc.sha256,
    )


# --------------------------------------------------------------------------- #
# Validation Results Endpoint
# --------------------------------------------------------------------------- #

@router.get("/validation", response_model=ValidationResultsResponse, summary="Validation Results Summary")
def get_validation_results() -> ValidationResultsResponse:
    """Returns the exact validation metrics, breakdowns, donut chart data, and flagged records."""
    stats = ValidationStats(
        total_records=585,
        valid_count=540,
        valid_percentage=92.3,
        needs_correction_count=28,
        needs_correction_percentage=4.8,
        flagged_count=17,
        flagged_percentage=2.9,
    )

    issues_breakdown = [
        IssueBreakdownItem(issue_type="Duplicate APAAR ID", count=8, percentage=1.4, color="#8B5CF6"),
        IssueBreakdownItem(issue_type="Invalid / Missing APAAR ID", count=12, percentage=2.1, color="#F97316"),
        IssueBreakdownItem(issue_type="Excess Enrolment", count=5, percentage=0.9, color="#EAB308"),
        IssueBreakdownItem(issue_type="Inconsistent Data", count=10, percentage=1.7, color="#06B6D4"),
        IssueBreakdownItem(issue_type="Possible Cross-Institution Duplicate", count=4, percentage=0.7, color="#10B981"),
        IssueBreakdownItem(issue_type="Others", count=3, percentage=0.5, color="#1E3A8A"),
    ]

    donut_data = ValidationDonutData(
        total_issues=42,
        items=[
            DonutLegendItem(label="Duplicate APAAR ID", percentage=19.0, color="#8B5CF6"),
            DonutLegendItem(label="Invalid / Missing", percentage=28.6, color="#F97316"),
            DonutLegendItem(label="Excess Enrolment", percentage=11.9, color="#EAB308"),
            DonutLegendItem(label="Inconsistent Data", percentage=23.8, color="#06B6D4"),
            DonutLegendItem(label="Cross-Institution Duplicate", percentage=9.5, color="#10B981"),
            DonutLegendItem(label="Others", percentage=7.1, color="#1E3A8A"),
        ],
    )

    return ValidationResultsResponse(
        date_range="24 Apr 2025 - 25 Apr 2025",
        stats=stats,
        issues_breakdown=issues_breakdown,
        donut_data=donut_data,
        flagged_records=_FLAGGED_RECORDS,
    )


# --------------------------------------------------------------------------- #
# Profile & Settings Endpoint
# --------------------------------------------------------------------------- #

@router.get("/profile", response_model=InstitutionProfile, summary="Get Institution Profile")
def get_profile() -> InstitutionProfile:
    return _PROFILE


@router.put("/profile", response_model=InstitutionProfile, summary="Update Institution Profile")
def update_profile(payload: UpdateInstitutionProfileRequest) -> InstitutionProfile:
    global _PROFILE
    _PROFILE = InstitutionProfile(
        institution_name=payload.institution_name,
        institution_id=_PROFILE.institution_id,
        aicte_approval_no=payload.aicte_approval_no,
        address=payload.address,
        contact_email=payload.contact_email,
        contact_number=payload.contact_number,
        academic_year=payload.academic_year,
        approved_intake=payload.approved_intake,
        logo_url=_PROFILE.logo_url,
    )
    return _PROFILE


# --------------------------------------------------------------------------- #
# User Management Endpoints
# --------------------------------------------------------------------------- #

_USERS_STORE: list[InstitutionalUser] = [
    InstitutionalUser(
        id="usr-1",
        name="Priya Verma",
        email="admin@xyzcollege.ac.in",
        role="Institution Admin",
        mfa_enabled=True,
        status="Active",
        last_login="Today, 10:45 AM",
    ),
    InstitutionalUser(
        id="usr-2",
        name="Rajesh Sharma",
        email="rajesh.s@xyzcollege.ac.in",
        role="Data Operator",
        mfa_enabled=True,
        status="Active",
        last_login="Yesterday, 04:20 PM",
    ),
    InstitutionalUser(
        id="usr-3",
        name="Ananya Joshi",
        email="ananya.j@xyzcollege.ac.in",
        role="Verification Officer",
        mfa_enabled=True,
        status="Active",
        last_login="23 Apr 2025, 11:15 AM",
    ),
]

@router.get("/users", response_model=list[InstitutionalUser], summary="List Institutional Users")
def list_users() -> list[InstitutionalUser]:
    return _USERS_STORE


@router.post("/users", response_model=InstitutionalUser, status_code=status.HTTP_201_CREATED, summary="Invite New User")
def invite_user(payload: CreateInstitutionalUserRequest) -> InstitutionalUser:
    new_user = InstitutionalUser(
        id=f"usr-{uuid.uuid4().hex[:6]}",
        name=payload.name.strip(),
        email=payload.email.strip().lower(),
        role=payload.role.strip(),
        mfa_enabled=True,
        status="Active",
        last_login="Invited (Pending)",
    )
    _USERS_STORE.append(new_user)
    return new_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete / Deactivate User")
def delete_user(user_id: str) -> None:
    global _USERS_STORE
    _USERS_STORE = [u for u in _USERS_STORE if u.id != user_id]


# --------------------------------------------------------------------------- #
# Data & Upload Endpoints
# --------------------------------------------------------------------------- #

_UPLOAD_BATCHES: list[UploadBatchItem] = [
    UploadBatchItem(
        id="bch-101",
        filename="students_admissions_btech_2025.xlsx",
        row_count=540,
        uploaded_by="Priya Verma",
        datetime="24 Apr 2025, 02:15 PM",
        status="Submitted",
    ),
    UploadBatchItem(
        id="bch-102",
        filename="lateral_entry_diploma_2025.xlsx",
        row_count=45,
        uploaded_by="Rajesh Sharma",
        datetime="23 Apr 2025, 11:30 AM",
        status="Ready",
    ),
    UploadBatchItem(
        id="bch-103",
        filename="pg_mba_admissions_batch1.xlsx",
        row_count=32,
        uploaded_by="Priya Verma",
        datetime="22 Apr 2025, 05:40 PM",
        status="Has Errors",
    ),
]

@router.get("/upload-batches", response_model=list[UploadBatchItem], summary="List Upload Batches")
def list_upload_batches() -> list[UploadBatchItem]:
    return _UPLOAD_BATCHES


@router.post("/upload", response_model=UploadDataResponse, summary="Upload & Validate Student File")
def upload_data() -> UploadDataResponse:
    batch_id = f"bch-{uuid.uuid4().hex[:6]}"
    new_batch = UploadBatchItem(
        id=batch_id,
        filename="batch_admissions_upload.xlsx",
        row_count=18,
        uploaded_by="Priya Verma",
        datetime="Just now",
        status="Ready",
    )
    _UPLOAD_BATCHES.insert(0, new_batch)
    return UploadDataResponse(
        batch_id=batch_id,
        filename="batch_admissions_upload.xlsx",
        row_count=18,
        valid_count=16,
        error_count=2,
        status="Ready",
        message="Batch validated successfully with 16 valid rows and 2 warnings.",
    )


@router.get("/api-key", summary="Get Institution API Key Details")
def get_api_key() -> dict[str, Any]:
    return {
        "institution_id": _PROFILE.institution_id,
        "key_prefix": "apaar_live_inst001_",
        "masked_key": "apaar_live_inst001_••••••••••••••••3a9f",
        "created_at": "15 Jan 2025",
        "last_used": "Today, 10:30 AM",
        "docs_url": "http://localhost:8000/docs",
    }


# --------------------------------------------------------------------------- #
# Notifications Preferences Endpoints
# --------------------------------------------------------------------------- #

_NOTIFICATIONS = NotificationPreferences()

@router.get("/notifications", response_model=NotificationPreferences, summary="Get Notification Preferences")
def get_notifications() -> NotificationPreferences:
    return _NOTIFICATIONS


@router.put("/notifications", response_model=NotificationPreferences, summary="Update Notification Preferences")
def update_notifications(payload: NotificationPreferences) -> NotificationPreferences:
    global _NOTIFICATIONS
    _NOTIFICATIONS = payload
    return _NOTIFICATIONS


# --------------------------------------------------------------------------- #
# Security & Access Control Endpoints
# --------------------------------------------------------------------------- #

_SECURITY = SecurityOverview()

@router.get("/security", response_model=SecurityOverview, summary="Get Security Overview")
def get_security() -> SecurityOverview:
    return _SECURITY


@router.post("/change-password", summary="Change Password")
def change_password(payload: ChangePasswordRequest) -> dict[str, str]:
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long.",
        )
    return {"status": "ok", "message": "Password updated successfully."}
