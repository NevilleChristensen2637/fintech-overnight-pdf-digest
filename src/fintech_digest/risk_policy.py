from decimal import Decimal

from .models import AuditNotification, PaymentEvent, PaymentStatus, RiskAction


MANUAL_REVIEW_AMOUNT = Decimal("10000")
HIGH_RISK_SCORE = 80


def decide_action(event: PaymentEvent) -> AuditNotification:
    if event.risk_score >= HIGH_RISK_SCORE:
        return AuditNotification(
            event_id=event.event_id,
            action=RiskAction.MANUAL_REVIEW,
            reason=f"risk score {event.risk_score} reached the review threshold",
        )
    if event.status is PaymentStatus.FAILED and event.amount >= MANUAL_REVIEW_AMOUNT:
        return AuditNotification(
            event_id=event.event_id,
            action=RiskAction.MANUAL_REVIEW,
            reason=f"failed payment of {event.currency} {event.amount} requires review",
        )
    if event.status is PaymentStatus.FAILED:
        return AuditNotification(
            event_id=event.event_id,
            action=RiskAction.NOTIFY_OPERATIONS,
            reason="failed payment requires an operations notification",
        )
    return AuditNotification(
        event_id=event.event_id,
        action=RiskAction.MONITOR,
        reason="no review threshold was reached",
    )

