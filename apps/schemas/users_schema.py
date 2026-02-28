from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from ..models.users_model import UserRole, UserPlan, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    plan: UserPlan = UserPlan.ESSENTIAL
    status: UserStatus = UserStatus.ACTIVE
    


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Minimum 8 characters")


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    plan: Optional[UserPlan] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None



class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    plan: UserPlan
    status: UserStatus
    cv_count: int
    last_activity: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "role": "user",
                "plan": "premium",
                "cv_count": 7,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    } 



class UserMini(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    plan: UserPlan

    model_config = {
        "from_attributes": True    
    }



class UserWithStats(UserResponse):
    average_cv_score: Optional[float] = None
    total_downloads: Optional[int] = None





# ===========================================================================
class TokenData(BaseModel):
    id : Optional[UUID] = None
    
    

class UserToken(BaseModel):
    access_token : str
    token_type : str

    model_config = {
        "from_attributes": True
    }    






class UserAdminListItem(BaseModel):
    id: UUID
    full_name: Optional[str]
    email: str
    plan: str
    status: str
    cv_count: int
    last_activity: Optional[datetime]

    class Config:
        from_attributes = True


class TutorStats(BaseModel):
    id: UUID
    full_name: Optional[str]
    tasks_assigned: int
    missions_completed: int
    retards: int
    delai_moyen_days: float
    status: str

    class Config:
        from_attributes = True
