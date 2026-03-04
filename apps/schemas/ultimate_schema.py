from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from ..models.ultimate_request import ReviewStatus


class UltimateRequestCreate(BaseModel):
    cv_id: UUID = Field(..., description="Which CV you need to review")
    job_description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Job description (optional - help provided by tutor)"
    )


class UltimateRequestResponse(BaseModel):
    id: UUID
    cv_id: UUID
    user_id: UUID
    job_description: Optional[str]
    status: ReviewStatus
    deadline: datetime
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True  
    }


class UltimateRequestStatus(BaseModel):
    id: UUID
    cv_id: UUID
    status: ReviewStatus
    deadline: datetime
    completed_at: Optional[datetime]
    assigned_tutor_id: Optional[UUID] = Field(
        None, description="ID of the tutor assigned to this request"
    )
    message: str = Field(default="Status fetched successfully")

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def from_orm_request(cls, request):
        """
        Helper to safely map ORM UltimateRequest -> UltimateRequestStatus
        avoiding ValidationError for missing attributes.
        """
        return cls(
            id=request.id,
            cv_id=request.cv_id,
            status=request.status,
            deadline=request.deadline,
            completed_at=request.completed_at,
            assigned_tutor_id=getattr(request, "tutor_id", None), 
            message="Status fetched successfully"
        )