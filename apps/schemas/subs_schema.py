from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateCheckoutRequest(BaseModel):
    plan: str = Field(..., pattern="^(starter|premium|ultimate)$")
    is_one_time: bool = Field(False, description="True only for Ultimate")


class CheckoutResponse(BaseModel):
    session_id: str
    url: str
    plan: str
    is_one_time: bool


class SubscriptionStatusResponse(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    message: str