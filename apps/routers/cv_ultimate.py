from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID
from datetime import datetime, timedelta
import logging
from ..models.cv_model import CV
from ..database import get_db
from ..models.users_model import User, UserPlan
from ..models.ultimate_request import UltimateRequest 
from ..schemas.ultimate_schema import UltimateRequestCreate, UltimateRequestResponse, UltimateRequestStatus

from ..authentication.users_oauth import get_current_user

router = APIRouter(
    prefix="/cv/ultimate", 
    tags=["CV Ultimate - Human Review"]
)

logger = logging.getLogger(__name__)



@router.post("/request", response_model=UltimateRequestResponse)
def request_human_review(
    request_data: UltimateRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if current_user.plan != UserPlan.ULTIMATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Human review is only available in ultimate plan. Please upgrade."
        )
    
    cv = db.query(CV).filter(CV.id == request_data.cv_id, CV.user_id == current_user.id).first()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found or you don't own this CV"
        )
    
    existing = db.query(UltimateRequest).filter(
        UltimateRequest.cv_id == request_data.cv_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review request already exists for this CV"
        )
    
    deadline = datetime.utcnow() + timedelta(days=7)
    new_request = UltimateRequest(
        user_id = current_user.id,
        cv_id = request_data.cv_id,
        job_description = request_data.job_description,
        status = "pending",
        deadline = datetime.utcnow() + timedelta(days=5)
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    logger.info(f"Human review requested for CV {request_data.cv_id} by user {current_user.id}")

    return UltimateRequestResponse.from_orm(new_request)



@router.get("/status/{request_id}", response_model=UltimateRequestStatus)
def get_review_status(
    request_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    request = db.query(UltimateRequest).filter(
        UltimateRequest.id == request_id,
        UltimateRequest.user_id == current_user.id
    ).first()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review request not found or not yours"
        )
    
    return UltimateRequestStatus.from_orm(request)