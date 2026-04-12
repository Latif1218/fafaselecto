from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from ..models.ultimate_request import ReviewStatus, PreferredDelay


class UltimateRequestCreate(BaseModel):
    cv_id: UUID = Field(..., description="Which CV you need to review")

    target_sector: Optional[str] = Field(
        None,
        max_length=150,
        description="Target sector for the review request"
    )

    target_position: Optional[str] = Field(
        None,
        max_length=150,
        description="Target position for the review request"
    )

    expectations: Optional[str] = Field(
        None,
        max_length=3000,
        description="User expectations for the review"
    )

    preferred_delay: Optional[PreferredDelay] = Field(
        None,
        description="Preferred review delay"
    )

    job_description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Job description (optional)"
    )

    cover_letter_id: Optional[UUID] = Field(
        None,
        description="Optional cover letter to attach with the review request"
    )


class UltimateRequestResponse(BaseModel):
    id: UUID
    cv_id: UUID
    user_id: UUID

    target_sector: Optional[str]
    target_position: Optional[str]
    expectations: Optional[str]
    preferred_delay: Optional[PreferredDelay]

    job_description: Optional[str]
    cover_letter_id: Optional[UUID]

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
        return cls(
            id=request.id,
            cv_id=request.cv_id,
            status=request.status,
            deadline=request.deadline,
            completed_at=request.completed_at,
            assigned_tutor_id=getattr(request, "assigned_tutor_id", None),
            message="Status fetched successfully"
        )