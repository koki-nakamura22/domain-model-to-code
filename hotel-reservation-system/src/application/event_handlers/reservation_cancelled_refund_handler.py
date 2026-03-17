"""予約キャンセル → 返金ハンドラ。"""

from __future__ import annotations

from src.domain.events.events import ReservationCancelled
from src.domain.services.payment_gateway import PaymentGateway


class ReservationCancelledRefundHandler:
    def __init__(self, payment_gateway: PaymentGateway) -> None:
        self._payment_gateway = payment_gateway

    async def handle(self, event: ReservationCancelled) -> None:
        if event.refund_amount.amount > 0:
            await self._payment_gateway.refund(
                amount=event.refund_amount,
                original_transaction_id=event.reservation_id,
            )
