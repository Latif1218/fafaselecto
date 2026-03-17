# utils/ultimate_stats.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from ..models.ultimate_request import UltimateRequest, ReviewStatus


def calculate_ultimate_stats(db: Session, days: int):

    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # On Hold
    on_hold = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.status == ReviewStatus.PENDING,
        UltimateRequest.created_at >= start_date
    ).scalar() or 0

    # Under Review
    under_review = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.status.in_([
            ReviewStatus.ASSIGNED,
            ReviewStatus.IN_PROGRESS
        ]),
        UltimateRequest.created_at >= start_date
    ).scalar() or 0

    # Completed
    completed = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.status == ReviewStatus.COMPLETED,
        UltimateRequest.created_at >= start_date
    ).scalar() or 0

    # Late (>72h)
    late = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.status == ReviewStatus.COMPLETED,
        UltimateRequest.completed_at > (UltimateRequest.deadline + timedelta(hours=72)),
        UltimateRequest.created_at >= start_date
    ).scalar() or 0

    return {
        "on_hold": on_hold,
        "under_review": under_review,
        "completed": completed,
        "late": late
    }