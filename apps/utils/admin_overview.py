from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta
from ..models.users_model import User, UserPlan
from ..models.ultimate_request import UltimateRequest, ReviewStatus

PLAN_PRICING = {
    UserPlan.STARTER: 10,
    UserPlan.PREMIUM: 20,
    UserPlan.ULTIMATE: 50
}


def calculate_admin_overview(db: Session):

    total_users = db.query(func.count(User.id)).scalar() or 0

    total_paying_users = db.query(func.count(User.id)).filter(
        User.plan != UserPlan.ESSENTIAL
    ).scalar() or 0

    total_requests = db.query(func.count(UltimateRequest.id)).scalar() or 0

    users = db.query(User.plan).all()

    mrr = 0
    for (plan,) in users:
        if plan in PLAN_PRICING:
            mrr += PLAN_PRICING[plan]

    late_applications = db.query(func.count(UltimateRequest.id)).filter(
        UltimateRequest.status == ReviewStatus.COMPLETED,
        UltimateRequest.completed_at > UltimateRequest.deadline
    ).scalar() or 0

    return {
        "total_users": total_users,
        "total_paying_users": total_paying_users,
        "total_ultimate_requests": total_requests,
        "mrr": mrr,
        "late_applications": late_applications
    }