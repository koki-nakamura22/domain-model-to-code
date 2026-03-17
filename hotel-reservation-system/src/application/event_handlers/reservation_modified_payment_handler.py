"""予約変更 → 差額決済/返金ハンドラ。"""

from __future__ import annotations

from src.domain.events.events import ReservationModified
from src.domain.services.payment_gateway import PaymentGateway


class ReservationModifiedPaymentHandler:
    def __init__(self, payment_gateway: PaymentGateway) -> None:
        self._payment_gateway = payment_gateway

    async def handle(self, event: ReservationModified) -> None:
        diff = event.amount_difference.amount
        if diff > 0:
            await self._payment_gateway.process(
                amount=event.amount_difference,
                method="CREDIT_CARD",
                card_info={},
            )
        elif diff < 0:
            from src.domain.models.shared import Money

            refund_amount = Money(amount=abs(diff), currency=event.amount_difference.currency)
            await self._payment_gateway.refund(
                amount=refund_amount,
                original_transaction_id=event.reservation_id,
            )
