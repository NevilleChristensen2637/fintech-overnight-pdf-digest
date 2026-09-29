from decimal import Decimal

from fintech_digest.models import PaymentEvent, RiskAction
from fintech_digest.risk_policy import decide_action


def test_large_failed_payment_requires_manual_review() -> None:
    event = PaymentEvent.model_validate(
        {
            "event_id": "pay_1042",
            "account_id": "merchant_88",
            "occurred_at": "2026-09-12T23:41:00Z",
            "amount": Decimal("12500.00"),
            "currency": "USD",
            "status": "failed",
            "risk_score": 62,
        }
    )

    notification = decide_action(event)

    assert notification.action is RiskAction.MANUAL_REVIEW
    assert notification.event_id == "pay_1042"
    assert "12500.00" in notification.reason

