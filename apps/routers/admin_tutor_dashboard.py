from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.users_model import User, UserRole
from ..schemas.admin_schema import AdminTutorStats
from ..utils.tutor_stats import calculate_tutor_stats
from ..authentication.users_oauth import get_current_admin_user


router = APIRouter(
    prefix="/admin/tutors",
    tags=["Admin - Tutor Dashboard"]
)


@router.get("/", response_model=List[AdminTutorStats])
def get_all_tutors(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):

    tutors = db.query(User).filter(User.role == UserRole.TUTOR).all()

    result = []

    for tutor in tutors:

        stats = calculate_tutor_stats(db, tutor.id)

        if tutor.status.value == "suspended":
            final_status = "Suspended"
        elif stats["average_delay_days"] < 1:
            final_status = "Excellent"
        else:
            final_status = "Active"

        result.append({
            "id": tutor.id,
            "full_name": tutor.full_name,
            "email": tutor.email,
            "tasks_assigned": stats["tasks_assigned"],
            "missions_completed": stats["missions_completed"],
            "delays": stats["delays"],
            "average_delay_days": stats["average_delay_days"],
            "status": final_status
        })

    return result



@router.get("/{tutor_id}", response_model=AdminTutorStats)
def get_single_tutor(
    tutor_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):

    tutor = db.query(User).filter(
        User.id == tutor_id,
        User.role == UserRole.TUTOR
    ).first()

    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Tutor not found"
        )

    stats = calculate_tutor_stats(db, tutor.id)

    return {
        "id": tutor.id,
        "full_name": tutor.full_name,
        "email": tutor.email,
        "tasks_assigned": stats["tasks_assigned"],
        "missions_completed": stats["missions_completed"],
        "delays": stats["delays"],
        "average_delay_days": stats["average_delay_days"],
        "status": tutor.status.value
    }




@router.delete("/{tutor_id}/hard")
def hard_delete_tutor(
    tutor_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):

    tutor = db.query(User).filter(
        User.id == tutor_id,
        User.role == UserRole.TUTOR
    ).first()

    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    db.delete(tutor)
    db.commit()

    return {"message": "Tutor deleted permanently"}