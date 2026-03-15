from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Annotated
from ..database import get_db
from ..models.users_model import User
from ..models.cv_model import CV
from ..utils.file_storage import get_file_url
from ..schemas.users_schema import UserResponse, UserUpdate, UserWithStats
from ..schemas.cv_schema import CVListItem
from ..authentication.users_oauth import get_current_user
from datetime import datetime




router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


@router.get("/me", response_model=UserWithStats)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )
    
    cv_stats = db.query(
        func.count(CV.id).label("cv_count"),
        func.avg(CV.score).label("avg_score")
    ).filter(
        CV.user_id == current_user.id
    ).first()

    return UserWithStats(
        id = current_user.id,
        email = current_user.email,
        full_name = current_user.full_name,
        role = current_user.role,
        plan = current_user.plan,
        status = current_user.status,
        cv_count = cv_stats.cv_count or 0,
        average_cv_score = float(cv_stats.avg_score or 0) if cv_stats.avg_score else None,
        last_activity = current_user.last_activity,
        created_at = current_user.created_at,
        updated_at = current_user.updated_at
    )




@router.patch("/update/me", response_model=UserResponse)
def update_my_profile(
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    update_dict = update_data.model_dump(exclude_unset=True)

    protected_fields = {"plan", "role", "status", "email"}
    for field in protected_fields:
        if field in update_dict:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot Update '{field}' field. Contact admin."
            )
        
    for key, value in update_dict.items():
        setattr(current_user, key, value)

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user




@router.get("/cvs_list/me", response_model=List[CVListItem])
def get_my_cvs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )

    query = db.query(CV).filter(CV.user_id == current_user.id)

    if sort_by == "score":
        order_column = CV.score
    elif sort_by == "title":
        order_column = CV.title
    else:
        order_column = CV.created_at

    if sort_order.lower() == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    cvs = query.offset(skip).limit(limit).all()

    if not cvs and skip > 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No more CVs found in this page"
        )

    cvs_response = [
        CVListItem(
            id=cv.id,
            title=cv.title,
            score=cv.score,
            domain=cv.domain,
            file_url=get_file_url(cv.file_path),
            download_url=f"/cv/{cv.id}/download",
            file_type=cv.file_type,
            is_favorite=cv.is_favorite,
            created_at=cv.created_at
        )
        for cv in cvs
    ]

    return cvs_response