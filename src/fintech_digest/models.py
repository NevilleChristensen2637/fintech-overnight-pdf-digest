from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class PaymentStatus(StrEnum):
    SETTLED = "settled"
    FAILED = "failed"
    PENDING = "pending"


class RiskAction(StrEnum):
    MONITOR = "monitor"
    NOTIFY_OPERATIONS = "notify_operations"
    MANUAL_REVIEW = "manual_review"


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    occurred_at: datetime
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    status: PaymentStatus
    risk_score: int = Field(ge=0, le=100)
    note: str = ""


class DigestRequest(BaseModel):
    run_id: str = Field(min_length=1)
    events: list[PaymentEvent] = Field(min_length=1, max_length=500)


class AuditNotification(BaseModel):
    event_id: str
    action: RiskAction
    reason: str


class DigestResponse(BaseModel):
    run_id: str
    reviewed_events: int
    notifications: list[AuditNotification]
    pdf_url: str

