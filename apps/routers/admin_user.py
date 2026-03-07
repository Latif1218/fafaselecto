from fastapi import HTTPException, status, APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Annotated, List
from datetime import datetime
from ..database import get_db
from ..authentication.users_oauth import get_current_admin_user
from ..models.users_model import User, UserPlan, UserRole, UserStatus
from ..schemas.admin_schema import UserListItem, UserListResponse, UserUpdateRequest, UserUpdateResponse, UserDeleteResponse
from uuid import UUID




router = APIRouter(
    prefix="/admin/users",
    tags=["Admin - Users"]
)


@router.get("/users", response_model=List[UserListItem])
def get_all_users(
    Current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None, description="Search by email or name"),
    role: UserRole = Query(None),
    plan: UserPlan = Query(None),
    status: UserStatus = Query(None)
):
    query = db.query(User)

    if search:
        search = f"%{search}"
        query = query.filter(
            (User.email.ilike(search)) | (User.full_name.ilike(search))
        )
    
    if role:
        query = query.filter(User.role == role)

    if plan:
        query = query.filter(User.plan == plan)

    if status:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    return UserListResponse(
        users=[UserListItem.from_orm(u) for u in users],
        total=total,
        page=(skip // limit) + 1,
        limit=limit
    )



@router.patch("/{user_id}", response_model=UserUpdateResponse)
async def update_user(
    user_id: UUID,
    update_data: UserUpdateRequest,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin connot update their own account via this endpoint"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_dict = update_data.dict(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update"
        )
    for key, value in update_dict.items():
        setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return UserUpdateResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        plan=user.plan,
        status=user.status,
        is_active=user.is_active
    )




@router.delete("/{user_id}", response_model=UserDeleteResponse)
async def soft_delete_user(
    user_id: UUID,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot delete their own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deactivated/soft-deleted"
        )
    
    user.is_active = False
    user.status = UserStatus.SUSPENDED
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    return UserDeleteResponse(id=user.id)