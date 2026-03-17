from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.ultimate_request import UltimateRequest, ReviewStatus


def calculate_tutor_stats(db: Session, tutor_id):

    # Assigned
    tasks_assigned = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.assigned_tutor_id == tutor_id
    ).scalar() or 0

    # Completed
    missions_completed = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.assigned_tutor_id == tutor_id,
        UltimateRequest.status == ReviewStatus.COMPLETED
    ).scalar() or 0

    # Delays
    delays = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.assigned_tutor_id == tutor_id,
        UltimateRequest.status == ReviewStatus.COMPLETED,
        UltimateRequest.completed_at > UltimateRequest.deadline
    ).scalar() or 0

    # Avg Delay (days)
    avg_delay = db.query(
        func.avg(
            func.extract(
                'epoch',
                UltimateRequest.completed_at - UltimateRequest.deadline
            ) / 86400
        )
    ).filter(
        UltimateRequest.assigned_tutor_id == tutor_id,
        UltimateRequest.completed_at > UltimateRequest.deadline
    ).scalar()

    average_delay_days = round(avg_delay, 2) if avg_delay else 0.0

    return {
        "tasks_assigned": tasks_assigned,
        "missions_completed": missions_completed,
        "delays": delays,
        "average_delay_days": average_delay_days
    }