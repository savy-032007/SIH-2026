"""Schemas for the Institution Portal (SPEC sections 5, 10.1)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #

class DashboardStats(BaseModel):
    approved_intake: int = 600
    actual_enrolment: int = 570
    remaining_seats: int = 30
    total_students: int = 585


class EnrolmentTrendPoint(BaseModel):
    year: str
    actual: int
    approved: int


class CategoryDistributionItem(BaseModel):
    category: str
    count: int
    percentage: float
    color: str


class RecentActivityItem(BaseModel):
    id: int
    activity: str
    details: str
    datetime: str
    type: Literal["success", "info", "alert"]


class DashboardResponse(BaseModel):
    institution_name: str = "XYZ College of Engineering"
    institution_id: str = "INST001"
    aicte_approval: str = "AICTE Approved"
    academic_year: str = "2025"
    admin_name: str = "Priya Verma"
    admin_role: str = "Institution Admin"
    stats: DashboardStats
    enrolment_trend: list[EnrolmentTrendPoint]
    category_distribution: list[CategoryDistributionItem]
    recent_activities: list[RecentActivityItem]


# --------------------------------------------------------------------------- #
# Students
# --------------------------------------------------------------------------- #

class StudentListItem(BaseModel):
    id: str
    row_num: int
    name: str
    apaar_id: str
    course: str
    year: str
    category: str
    status: Literal["Valid", "Needs Correction", "Flagged"]
    student_id_college: str | None = None
    gender: str | None = None
    dob: str | None = None


class StudentListResponse(BaseModel):
    students: list[StudentListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class CreateStudentRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Student Name")
    apaar_id: str = Field(..., min_length=12, max_length=12, description="12-digit APAAR ID")
    dob: str = Field(..., description="Date of Birth YYYY-MM-DD or DD/MM/YYYY")
    gender: str = Field(..., description="Gender: Male, Female, Other")
    course: str = Field(..., description="Course name, e.g. B.Tech CSE")
    admission_year: str = Field(default="2025", description="Academic Year")
    student_id_college: str = Field(..., description="College student ID / Roll No.")
    nri_category: str = Field(default="No")
    oci_status: str = Field(default="No")
    foreign_national: str = Field(default="No")
    supernumerary_seats: int = Field(default=0)
    remarks: str | None = None


class VerifyApaarRequest(BaseModel):
    apaar_id: str
    name: str | None = None
    dob: str | None = None


class VerifyApaarResponse(BaseModel):
    apaar_id: str
    valid: bool
    exists: bool
    masked_name: str | None = None
    status: str
    message: str


# --------------------------------------------------------------------------- #
# Validation Results
# --------------------------------------------------------------------------- #

class ValidationStats(BaseModel):
    total_records: int = 585
    valid_count: int = 540
    valid_percentage: float = 92.3
    needs_correction_count: int = 28
    needs_correction_percentage: float = 4.8
    flagged_count: int = 17
    flagged_percentage: float = 2.9


class IssueBreakdownItem(BaseModel):
    issue_type: str
    count: int
    percentage: float
    color: str


class DonutLegendItem(BaseModel):
    label: str
    percentage: float
    color: str


class ValidationDonutData(BaseModel):
    total_issues: int = 42
    items: list[DonutLegendItem]


class FlaggedRecordItem(BaseModel):
    id: str
    row_num: int
    student_name: str
    apaar_id: str
    issue: str
    status: Literal["Needs Correction", "Flagged"]
    details: str | None = None


class ValidationResultsResponse(BaseModel):
    date_range: str = "24 Apr 2025 - 25 Apr 2025"
    stats: ValidationStats
    issues_breakdown: list[IssueBreakdownItem]
    donut_data: ValidationDonutData
    flagged_records: list[FlaggedRecordItem]


# --------------------------------------------------------------------------- #
# Settings & Profile
# --------------------------------------------------------------------------- #

class InstitutionProfile(BaseModel):
    institution_name: str = "XYZ College of Engineering"
    institution_id: str = "INST001"
    aicte_approval_no: str = "1-12345678901"
    address: str = "123 College Road, Pune, Maharashtra, India - 411001"
    contact_email: str = "admin@xyzcollege.ac.in"
    contact_number: str = "+91 9876543210"
    academic_year: str = "2025"
    approved_intake: int = 600
    logo_url: str = "/aicte-logo.png"


class UpdateInstitutionProfileRequest(BaseModel):
    institution_name: str
    aicte_approval_no: str
    address: str
    contact_email: str
    contact_number: str
    academic_year: str
    approved_intake: int


# --------------------------------------------------------------------------- #
# User Management Schemas
# --------------------------------------------------------------------------- #

class InstitutionalUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    mfa_enabled: bool
    status: Literal["Active", "Inactive"]
    last_login: str


class CreateInstitutionalUserRequest(BaseModel):
    name: str
    email: str
    role: str


# --------------------------------------------------------------------------- #
# Data & Upload Schemas
# --------------------------------------------------------------------------- #

class UploadBatchItem(BaseModel):
    id: str
    filename: str
    row_count: int
    uploaded_by: str
    datetime: str
    status: Literal["Submitted", "Ready", "Has Errors", "Validating"]


class UploadDataResponse(BaseModel):
    batch_id: str
    filename: str
    row_count: int
    valid_count: int
    error_count: int
    status: str
    message: str


# --------------------------------------------------------------------------- #
# Notification Preferences Schemas
# --------------------------------------------------------------------------- #

class NotificationPreferences(BaseModel):
    validation_anomalies: bool = True
    cross_institution_flags: bool = True
    digilocker_consent_updates: bool = True
    aicte_circulars: bool = True
    critical_sms_alerts: bool = True
    phone_number: str = "+91 9876543210"


# --------------------------------------------------------------------------- #
# Security & Password Schemas
# --------------------------------------------------------------------------- #

class SecurityOverview(BaseModel):
    mfa_enforced: bool = True
    mfa_configured: bool = True
    mfa_method: str = "Authenticator App (TOTP)"
    last_password_change: str = "24 Jan 2025"
    active_session_ip: str = "192.168.1.45 (Pune, MH)"
    audit_chain_status: str = "Intact (SHA-256 Verified)"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
