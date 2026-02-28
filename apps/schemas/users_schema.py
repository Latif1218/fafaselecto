from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"
    plan: str = "essential"
    status: str = "active"
    


class UserCreate(UserBase):
    password: str


class UserRespons(BaseModel):
    id: UUID
    email: EmailStr
    
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    } 


class TokenData(BaseModel):
    id : Optional[UUID] = None
    
    

class UserToken(BaseModel):
    access_token : str
    token_type : str

    model_config = {
        "from_attributes": True
    }    



class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    plan: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


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
