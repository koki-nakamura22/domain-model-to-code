"""Paymentリポジトリインターフェース。"""

from __future__ import annotations

from typing import Protocol

from src.domain.models.payment import Payment


class PaymentRepository(Protocol):
    async def find_by_id(self, payment_id: str) -> Payment | None: ...
    async def find_by_reservation_id(self, reservation_id: str) -> list[Payment]: ...
    async def save(self, payment: Payment) -> None: ...
