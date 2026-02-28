from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime


class CVTips(BaseModel):
    category: str
    message: str
    priority: int = Field(..., ge=1, le=3)    #1=low, 2=medium, 3=high

class CVEvaluationResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    color: str 
    tips: List[CVTips]
    message: str


class CVListItem(BaseModel):
    id: UUID
    title: Optional[str]
    score: Optional[int]
    file_url: str
    file_type: str
    is_favorite: bool
    created_at: datetime

    model_config = {
        "from_attributes":True
    }



class CVDetail(CVListItem):
    tips: Optional[List[CVTips]] = None
    raw_metadata: Optional[Dict] = None



class CVGenerateResponse(BaseModel):
    cv_id: UUID
    pdf_url: str
    docx_url: Optional[str] = None
    language: str
    message: str


# ============================================================================

class CVFormData(BaseModel):
    """Comming from multi-step form"""
    personal_details: Dict[str, Any]   
    education: List[Dict[str, Any]]    
    employment: List[Dict[str, Any]]   
    languages: List[Dict[str, Any]]    
    skills: List[Dict[str, Any]]       
    activities: List[Dict[str, Any]]



class CVGenerateRequest(BaseModel):
    form_data: CVFormData
    format: str = "pdf"


class CoverLetterRequest(BaseModel):
    reference_cv_id: str
    job_description: Optional[str] = None
    format: str = "pdf"

class CVDashboardItem(BaseModel):
    id: str
    title: Optional[str] = None
    score: Optional[int] = None
    file_url: str
    created_at: str