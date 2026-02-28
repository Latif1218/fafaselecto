from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime


class PersonalDetails(BaseModel):
    Job_Type: str
    full_name: str
    email: EmailStr
    date_of_birth: str
    Job_Type: str
    phone_number: str
    address: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    photo_url: Optional[str] = None


class EducationEntry(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None
    description: str


class EmploymentEntry(BaseModel):
    position: str
    company: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    bullets: List[str]
    description: str


class LanguageEntry(BaseModel):
    language: str
    level: Optional[str] = None


class SkillEntry(BaseModel):
    activity_name: str
    level: Optional[str] = None


class ActivityEntry(BaseModel):
    title: str
    description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CVFormPartial(BaseModel):
    """Single step update"""
    personal_details: Optional[PersonalDetails] = None
    education: Optional[List[EducationEntry]] = None
    employment: Optional[List[EmploymentEntry]] = None
    language: Optional[List[LanguageEntry]] = None
    skills: Optional[List[SkillEntry]] = None
    activities: Optional[List[ActivityEntry]] = None


class CVFormFull(BaseModel):
    """Complete form structure"""
    personal_details: PersonalDetails
    education: List[EducationEntry]
    employment: List[EmploymentEntry]
    language: List[LanguageEntry]
    skills: List[SkillEntry]
    activities: List[ActivityEntry]


class CVFormResponse(BaseModel):
    id: UUID
    last_updated_step: Optional[str] 
    is_complete: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

    
