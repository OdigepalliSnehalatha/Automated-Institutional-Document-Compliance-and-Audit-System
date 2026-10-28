from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: str
    password: str
    institution_name: Optional[str] = "Anantha Lakshmi Institute of Technology and Sciences"
    role: Optional[str] = None  # Ignored for security; role verified directly from database

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str
    institution_name: Optional[str] = "Anantha Lakshmi Institute of Technology and Sciences"
    role: Optional[str] = None

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "Faculty"
    department_id: Optional[int] = None
    institution_name: Optional[str] = "Anantha Lakshmi Institute of Technology and Sciences"

class VerifyRegistrationRequest(BaseModel):
    email: str
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: str
    institution_name: Optional[str] = "Anantha Lakshmi Institute of Technology and Sciences"

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class UserCreateRequest(BaseModel):
    name: str
    email: str
    password: Optional[str] = "Default@123"
    role: str
    department_id: Optional[int] = None
    is_active: bool = True

class UserRoleUpdateRequest(BaseModel):
    role: str
    department_id: Optional[int] = None

class UserStatusUpdateRequest(BaseModel):
    is_active: bool

class FormatRequirementItem(BaseModel):
    id: Optional[int] = None
    requirement_name: str
    requirement_type: str
    requirement_value: Optional[str] = ""
    is_required: bool = True
    display_order: int = 1

class FormatCreateRequest(BaseModel):
    institution_id: int
    department_id: Optional[int] = None
    document_type_id: int
    format_name: str
    instructions: Optional[str] = None
    requirements: List[FormatRequirementItem] = []

class FormatUpdateRequest(BaseModel):
    format_name: Optional[str] = None
    instructions: Optional[str] = None
    department_id: Optional[int] = None
    requirements: Optional[List[FormatRequirementItem]] = None

class ValidationReportItem(BaseModel):
    requirement: str
    expected_value: str
    detected_value: str
    result: str  # "Correct", "Incorrect", "Missing", "Needs Review", "Not Applicable"
    explanation: str
    recommended_correction: str

class ValidationSummary(BaseModel):
    total_checks: int
    passed_checks: int
    failed_checks: int
    missing_requirements: int
    needs_review: int
    compliance_percentage: float
    validation_status: str  # "VALID", "INVALID", "NEEDS_REVIEW"

class ValidationReportResponse(BaseModel):
    document_id: int
    file_name: str
    exam_category: Optional[str] = None
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    overall_status: str
    approval_status: str
    compliance_percentage: float
    summary: ValidationSummary
    items: List[ValidationReportItem]
    analyzed_at: Optional[str] = None

class QuestionPaperDecisionRequest(BaseModel):
    decision: str  # "ACCEPTED", "REJECTED", "NEEDS_REVIEW"
    comments: Optional[str] = None

class CourseCreateRequest(BaseModel):
    department_id: int
    semester_id: int
    course_code: str
    course_name: str
    credits: Optional[int] = 3
    academic_year_id: Optional[int] = None

class FacultyAssignmentRequest(BaseModel):
    course_id: int
    faculty_id: int
    academic_year_id: Optional[int] = None

class RequirementResultItem(BaseModel):
    name: str
    required: bool = True
    status: str  # "PASS" or "FAIL"
    reason: Optional[str] = None

class AnalysisResult(BaseModel):
    status: str  # "ACCEPTED" or "REJECTED" or "NEEDS_REVIEW"
    requirements: List[RequirementResultItem]
    analyzed_at: Optional[str] = None
