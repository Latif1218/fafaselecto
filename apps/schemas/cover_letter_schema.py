from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CoverLetterGenerateRequest(BaseModel):
    cv_id: UUID
    job_description: str
    job_link: Optional[str] = None
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"
    language: Optional[str] = "en"
    title: Optional[str] = "Cover Letter"


class CoverLetterResponse(BaseModel):
    id: UUID
    cv_id: Optional[UUID] = None
    title: Optional[str] = None
    job_description: Optional[str] = None
    job_link: Optional[str] = None
    content: str
    file_url: Optional[str] = None
    language: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }