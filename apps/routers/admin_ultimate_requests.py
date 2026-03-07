from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID
from datetime import datetime
from ..database import get_db
from ..models.users_model import User, UserRole
from ..models.ultimate_request import UltimateRequest, ReviewStatus
from ..authentication.users_oauth import get_current_admin_user
from ..schemas.admin_schema import UltimateRequestListItem, UltimateRequestListResponse, AssignTutorRequest, AssignTutorResponse, ValidateRequest, ValidateResponse


router = APIRouter(
    prefix="/admin/ultimate-requests", 
    tags=["Admin - Ultimate Requests"]
)

@router.get("/", response_model=UltimateRequestListResponse)
async def get_ultimate_requests(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: ReviewStatus = Query(None),
    search: str = Query(None)
):
    """
    Get paginated list of all ultimate review requests with proper alias handling.
    """
    query = db.query(UltimateRequest)

    if status:
        query = query.filter(UltimateRequest.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.join(User, UltimateRequest.user_id == User.id, aliased=True)  
        query = query.filter(
            (User.email.ilike(search_term)) |
            (UltimateRequest.job_description.ilike(search_term))
        )

    total = query.count()

    from sqlalchemy.orm import aliased

    UserAlias = aliased(User, name="requester")
    TutorAlias = aliased(User, name="tutor")

    query = (
        db.query(UltimateRequest)
        .outerjoin(UserAlias, UltimateRequest.user_id == UserAlias.id)
        .outerjoin(TutorAlias, UltimateRequest.assigned_tutor_id == TutorAlias.id)
        .offset(skip)
        .limit(limit)
    )

    requests = query.all()

    formatted_requests = []
    for req in requests:
        formatted_requests.append(
            UltimateRequestListItem(
                id=req.id,
                user_id=req.user_id,
                user_email=req.requester.email if hasattr(req, 'requester') and req.requester else None,
                cv_id=req.cv_id,
                job_description=req.job_description,
                status=req.status,
                assigned_tutor_id=req.assigned_tutor_id,
                tutor_name=req.tutor.full_name if hasattr(req, 'tutor') and req.tutor else None,
                deadline=req.deadline,
                created_at=req.created_at,
                completed_at=req.completed_at
            )
        )

    return UltimateRequestListResponse(
        requests=formatted_requests,
        total=total,
        page=(skip // limit) + 1,
        limit=limit
    )



@router.post("/{request_id}/assign", response_model=AssignTutorResponse)
async def assign_tutor_to_request(
    request_id: UUID,
    assign_data: AssignTutorRequest,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)]
):
    request = db.query(UltimateRequest).filter(UltimateRequest.id == request_id).first()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review request not found."
        )
    
    if request.status != ReviewStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request is not Pending status."
        )
    
    tutor = db.query(User).filter(User.id == assign_data.tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found."
        )
    
    if tutor.role != UserRole.TUTOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user is not a tutor."
        )
    
    request.assigned_tutor_id = assign_data.tutor_id
    request.status = ReviewStatus.ASSIGNED
    request.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(request)

    return AssignTutorResponse(
        request_id=request.id,
        tutor_id=tutor.id,
        status=request.status
    )




@router.post("{request_id}/validate", response_model=ValidateResponse)
async def validate_ultimate_request(
    request_id: UUID,
    validate_data: ValidateRequest,
    ccurrent_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)]
):
    request = db.query(UltimateRequest).filter(UltimateRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review request not found"
        )
    if request.status not in [ReviewStatus.ASSIGNED, ReviewStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Request must be assigned or in progress to validate"
        )
    
    if validate_data.action == "approve":
        request.status = ReviewStatus.COMPLETED
    elif validate_data.action == "reject":
        request.status = ReviewStatus.REJECTED
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action: must be 'approve' or 'reject'"
        )
    
    request.completed_at = datetime.utcnow()
    request.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(request)

    return ValidateResponse(
        request_id=request.id,
        status=request.status
    )