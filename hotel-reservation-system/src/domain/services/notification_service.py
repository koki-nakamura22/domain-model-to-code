"""通知サービスProtocol。"""

from __future__ import annotations

from typing import Protocol

from src.domain.models.reservation import StayPeriod
from src.domain.models.shared import Money


class NotificationService(Protocol):
    async def send_reservation_confirmed(
        self, guest_id: str, reservation_number: str, stay_period: StayPeriod, total_amount: Money
    ) -> None: ...

    async def send_reservation_modified(
        self,
        guest_id: str,
        reservation_number: str,
        new_stay_period: StayPeriod,
        new_total_amount: Money,
        amount_difference: Money,
    ) -> None: ...

    async def send_reservation_cancelled(
        self, guest_id: str, reservation_number: str, cancellation_fee: Money, refund_amount: Money
    ) -> None: ...

    async def send_no_show_detected(self, guest_id: str, reservation_number: str, total_amount: Money) -> None: ...

    async def send_payment_failed(self, reservation_id: str, reason: str) -> None: ...
