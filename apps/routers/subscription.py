import stripe
import uuid
import logging
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..models.users_model import User
from ..models.subs_model import Subscription, PlanType, SubscriptionStatus
from ..schemas.subs_schema import CreateCheckoutRequest, CheckoutResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..authentication.users_oauth import get_current_user
from ..config import STRIPE_SECRET_KEY, STRIPE_SUCCESS_URL, STRIPE_CANCEL_URL, PRICE_IDS, STRIPE_WEBHOOK_SECRET
import os


router = APIRouter(
    prefix="/subscription", 
    tags=["Subscription"]
)


stripe.api_key = STRIPE_SECRET_KEY
stripe.api_version = "2024-06-20" 


logger = logging.getLogger(__name__)


PRICE_IDS = {
    "starter": {"monthly": os.getenv("PRICE_STARTER_MONTHLY")},
    "premium": {"monthly": os.getenv("PRICE_PREMIUM_MONTHLY")},
    "ultimate": {"one_time": os.getenv("PRICE_ULTIMATE_ONETIME")}
}
for plan, prices in PRICE_IDS.items():
    for key, value in prices.items():
        if not value:
            logger.warning(f"Missing Stripe Price ID for {plan} {key}")



@router.get("/config")
async def get_payment_config():
    """Frontend pricing page-Stripe config + plan prices."""
    return {
        "publishableKey": os.getenv("STRIPE_PUBLISHABLE_KEY"),
        "plans": {
            "essential": {"price": 0.00, "currency": "EUR", "note": "Free plan"},
            "starter": {"monthly": PRICE_IDS["starter"]["monthly"], "price": 4.90, "currency": "EUR"},
            "premium": {"monthly": PRICE_IDS["premium"]["monthly"], "price": 24.90, "currency": "EUR"},
            "ultimate": {"one_time": PRICE_IDS["ultimate"]["one_time"], "price": 149.00, "currency": "EUR"}
        }
    }




@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    req: CreateCheckoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Create Stripe Checkout session for plan upgrade or Ultimate one-time payment.
    """
    plan = req.plan.lower()

    if plan not in ["starter", "premium", "ultimate"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan selected. Must be 'starter', 'premium' or 'ultimate'"
        )

    if plan == "ultimate" and not req.is_one_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ultimate plan is one-time payment only"
        )

    try:
        if plan == "ultimate":
            price_id = PRICE_IDS["ultimate"]["one_time"]
            mode = "payment"
        else:
            price_id = PRICE_IDS[plan]["monthly"]
            mode = "subscription"
    except KeyError:
        logger.error(f"Missing price ID for plan: {plan}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment configuration error - contact support"
        )

    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            payment_method_types=["card"],
            customer_email=current_user.email,
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={
                "user_id": str(current_user.id),
                "email": current_user.email,
                "plan": plan,
                "is_one_time": str(req.is_one_time)
            },
            success_url=STRIPE_SUCCESS_URL,
            cancel_url=STRIPE_CANCEL_URL,
        )

        sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()

        if not sub:
            sub = Subscription(
                id=str(uuid.uuid4()), 
                stripe_subscription_id=session.subscription or session.id,  
                user_id=current_user.id,
                stripe_customer_id=session.customer,
                plan_type=PlanType(plan),
                price_id=price_id,
                status=SubscriptionStatus.INCOMPLETE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(sub)
        else:
            sub.plan_type = PlanType(plan)
            sub.price_id = price_id
            sub.status = SubscriptionStatus.INCOMPLETE
            sub.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(sub)

        logger.info(f"Checkout session created | User: {current_user.id} | Plan: {plan} | Mode: {mode}")

        return CheckoutResponse(
            session_id=session.id,
            url=session.url,
            plan=plan,
            is_one_time=req.is_one_time
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e.user_message or str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment setup failed: {e.user_message or str(e)}"
        )
    except Exception as e:
        logger.exception("Checkout error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during checkout"
        )
    


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    payload = await request.body()
    
    sig_header = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configure"
        )

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"].get("user_id")
        plan = session["metadata"].get("plan")

        if not user_id or not plan:
            logger.warning("Webhook missing metadata")
            return {"status": "ignored"}

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "user not found"}

        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

        if not sub:
            sub = Subscription(
                id=session.subscription or session.id,
                user_id=user.id,
                stripe_customer_id=session.customer,
                plan_type=PlanType(plan),
                price_id=session["line_items"]["data"][0]["price"]["id"],
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.fromtimestamp(session.get("subscription_details", {}).get("current_period_start")) if "subscription_details" in session else None,
                current_period_end=datetime.fromtimestamp(session.get("subscription_details", {}).get("current_period_end")) if "subscription_details" in session else None,
            )
            db.add(sub)
        else:
            sub.plan_type = PlanType(plan)
            sub.status = SubscriptionStatus.ACTIVE
            sub.updated_at = datetime.utcnow()

        db.commit()
        logger.info(f"Plan upgraded | User: {user_id} | Plan: {plan}")

    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        sub_id = invoice.subscription
        sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
        if sub:
            sub.status = SubscriptionStatus.ACTIVE
            db.commit()

    elif event["type"] == "customer.subscription.deleted":
        sub_id = event["data"]["object"]["id"]
        sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
        if sub:
            sub.status = SubscriptionStatus.CANCELED
            db.commit()

    return {"status": "success"}