from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class CoverLetterWarning(BaseModel):
    code: str
    message: str
    severity: str = Field(default="warning")


class CoverLetterGenerateRequest(BaseModel):
    cv_id: Optional[UUID] = None
    job_description: Optional[str] = None
    job_link: Optional[str] = None
    language: Optional[str] = None
    title: Optional[str] = "Cover Letter"


class CoverLetterResponse(BaseModel):
    id: UUID
    cv_id: Optional[UUID] = None
    title: Optional[str] = None
    job_description: Optional[str] = None
    job_link: Optional[str] = None
    company_name: Optional[str] = None
    position_title: Optional[str] = None
    content: str
    language: str
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None
    preview_url: Optional[str] = None
    warnings: List[CoverLetterWarning] = []
    created_at: datetime

    model_config = {
        "from_attributes": True
    }