from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CoverLetterGenerateRequest(BaseModel):
    cv_id: UUID
    job_description: str
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"
    language: Optional[str] = "en"
    title: Optional[str] = "Cover Letter"


class CoverLetterResponse(BaseModel):
    id: UUID
    cv_id: UUID
    content: str
    file_url: Optional[str]
    language: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }