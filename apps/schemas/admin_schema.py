from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum
from ..models.users_model import UserRole, UserPlan, UserStatus
from ..models.ultimate_request import ReviewStatus


class UserListItem(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    plan: UserPlan
    status: UserStatus
    cv_count: int
    is_active: bool
    created_at: datetime
    last_activity: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True
    )


class UserListResponse(BaseModel):
    users: List[UserListItem]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(
        from_attributes=True
    )


class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    plan: Optional[UserPlan] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None


class UserUpdateResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    plan: UserPlan
    status: UserStatus
    is_active: bool
    message: str = "User update successfully"


class UserDeleteResponse(BaseModel):
    id: UUID
    message: str = "User soft deleted successfully"
    


class UltimateRequestListItem(BaseModel):
    id: UUID
    user_id: UUID
    user_email: Optional[str]  
    cv_id: UUID
    job_description: Optional[str]
    status: ReviewStatus
    assigned_tutor_id: Optional[UUID]
    tutor_name: Optional[str]
    deadline: datetime
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class UltimateRequestListResponse(BaseModel):
    requests: List[UltimateRequestListItem]
    total: int
    page: int
    limit: int


class AssignTutorRequest(BaseModel):
    tutor_id: UUID = Field(..., description="ID of the tutor to assign")


class AssignTutorResponse(BaseModel):
    request_id: UUID
    tutor_id: UUID
    status: ReviewStatus
    message: str = "Tutor assigned successfully"


class ValidateRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$", description="approve or reject")
    comment: Optional[str] = None


class ValidateResponse(BaseModel):
    request_id: UUID
    status: ReviewStatus
    message: str = "Request validated successfully"