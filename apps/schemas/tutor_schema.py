from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.ultimate_request import ReviewStatus



class TutorRequestListItem(BaseModel):
    id: UUID
    user_email: Optional[str]
    cv_title: Optional[str]
    job_description: Optional[str]
    status: ReviewStatus
    deadline: datetime
    created_at: datetime
    assigned_at: Optional[datetime]

    class Config:
        from_attributes = True



class TutorRequestListResponse(BaseModel):
    requests: List[TutorRequestListItem]
    total: int
    page: int
    limit: int



class TutorRequestDetail(BaseModel):
    id: UUID
    user_id: UUID
    user_email: Optional[str]
    user_full_name: Optional[str]
    cv_id: UUID
    cv_title: Optional[str]
    cv_file_url: Optional[str]
    job_description: Optional[str]
    status: ReviewStatus
    deadline: datetime
    created_at: datetime
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True



class ReviewSubmitRequest(BaseModel):
    comment: str = Field(..., min_length=20, description="Tutor's revew comment")
    score: int = Field(..., ge=0, le=100, description="CV score out of 100")



class ReviewSubmitResponse(BaseModel):
    request_id: UUID
    status: ReviewStatus
    message: str = "Review submitted successfully"