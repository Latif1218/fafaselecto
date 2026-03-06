from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID
from datetime import datetime
from ..database import get_db
from ..models.users_model import User
from ..models.ultimate_request import UltimateRequest, ReviewStatus
from ..models.cv_model import CV
from..authentication.users_oauth import get_current_tutor_user
from ..utils.file_storage import save_uploaded_file, get_file_url
from ..schemas.tutor_schema import TutorRequestListItem, TutorRequestListResponse, TutorRequestDetail, ReviewSubmitRequest, ReviewSubmitResponse



router = APIRouter(
    prefix="/tutor",
    tags=["Tutor - Requests"]
)



@router.get("/requests", response_model=TutorRequestListResponse)
async def get_my_assigned_requests(
    current_tutor: Annotated[User, Depends(get_current_tutor_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: ReviewStatus = Query(None, description="Filter by status")
):
    query = db.query(UltimateRequest).filter(
        UltimateRequest.assigned_tutor_id == current_tutor.id
    )

    if status:
        query = query.filter(UltimateRequest.status == status)
        total = query.count()

        requests = (
            query.join(CV, UltimateRequest.cv_id == CV.id, isouter=True).join(
                User, UltimateRequest.user_id == User.id, isouter=True
            ).offset(skip).limit(limit).all()
        )

        formatted = []
        for req in requests:
            formatted.append(
                TutorRequestListItem(
                    id = req.id,
                    user_email=req.user.email if req.user else None,
                    cv_title=req.cv.title if req.cv else None,
                    job_description=req.job_description,
                    status=req.status,
                    deadline=req.deadline,
                    created_at=req.created_at,
                    assigned_at=req.updated_at
                )
            )
        return TutorRequestListResponse(
            requests=formatted,
            total=total,
            page=(skip // limit) + 1,
            limit=limit
        )
    


@router.get("/requests/{id}", response_model=TutorRequestDetail)
async def get_request_detail(
        id: UUID,
        current_tutor: Annotated[User, Depends(get_current_tutor_user)],
        db: Annotated[Session, Depends(get_db)]
):
    request = (
        db.query(UltimateRequest).filter(
            UltimateRequest.id == id,
            UltimateRequest.assigned_tutor_id == current_tutor.id
        ).join(CV, UltimateRequest.cv_id == CV.id, isouter=True).join(
            User, UltimateRequest.user_id == User.id, isouter=True
        ).first()
    )

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found or not assigned to you."
        )
    
    return TutorRequestDetail(
        id=request.id, 
        user_id=request.user_id,
        user_email=request.user.email if request.user else None,
        user_full_name=request.user.full_name if request.user else None,
        cv_id = request.cv_id,
        cv_title=request.cv.title if request.cv else None,
        cv_file_url=get_file_url(request.cv.file_path) if request.cv and request.cv.file_path else None,
        job_description=request.job_description,
        status=request.status,
        deadline=request.deadline,
        created_at=request.created_at,
        assigned_at=request.updated_at,
        completed_at=request.completed_at
    )



@router.post("/reviews/{request_id}", response_model=ReviewSubmitResponse)
async def submit_review(
    request_id: UUID,
    review_data: ReviewSubmitRequest,
    current_tutor: Annotated[User, Depends(get_current_tutor_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...)
):
    request = db.query(UltimateRequest).filter(
        UltimateRequest.id == request_id,
        UltimateRequest.assigned_tutor_id == current_tutor.id
    ).first()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found or not assigned to you"
        )
    
    if request.status not in [ReviewStatus.ASSIGNED, ReviewStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request must be assigned or in progress to submit review."
        )
    
    allowed_extensions = {".pdf", ".docx"}
    ext = file.filename.lower()[-5:]
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF or DOCX files allowed"
        )
    
    # file_path = await save_uploaded_file(
    #     file,
    #     folder="reviews",
    #     user_id=str(current_tutor.id),
    #     request_id=str(request_id)
    # )

    request.status = ReviewStatus.COMPLETED
    request.completed_at = datetime.utcnow()
    request.updated_at = datetime.utcnow()
    # request.review_file_path = file_path
    # request.review_score = review_data.score
    # request.review_comment = review_data.comment

    db.commit()
    db.refresh(request)

    return ReviewSubmitResponse(
        request_id=request.id,
        status=request.status
    )