from typing import List, Optional, Any
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    institution_name: str
    role: str
    email: str
    password: Optional[str] = None

class VerifyOTPRequest(BaseModel):
    institution_name: str
    role: str
    email: str
    otp: str

class UserCreateRequest(BaseModel):
    name: str
    email: str
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

class RequirementResultItem(BaseModel):
    name: str
    required: bool = True
    status: str  # "PASS" or "FAIL"
    reason: Optional[str] = None

class AnalysisResult(BaseModel):
    status: str  # "ACCEPTED" or "REJECTED"
    requirements: List[RequirementResultItem]
    analyzed_at: Optional[str] = None
