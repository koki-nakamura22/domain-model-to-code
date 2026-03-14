"""Payment集約: 決済処理の管理。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum

from src.domain.models.shared import Money, new_id


class PaymentStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"


@dataclass
class Payment:
    id: str
    reservation_id: str
    amount: Money
    status: PaymentStatus
    method: PaymentMethod
    processed_at: datetime.datetime | None = None

    @staticmethod
    def create(reservation_id: str, amount: Money, method: PaymentMethod) -> Payment:
        return Payment(
            id=new_id(),
            reservation_id=reservation_id,
            amount=amount,
            status=PaymentStatus.PENDING,
            method=method,
        )

    def complete(self) -> None:
        self._assert_status(PaymentStatus.PENDING)
        self.status = PaymentStatus.COMPLETED
        self.processed_at = datetime.datetime.now(tz=datetime.UTC)

    def fail(self) -> None:
        self._assert_status(PaymentStatus.PENDING)
        self.status = PaymentStatus.FAILED
        self.processed_at = datetime.datetime.now(tz=datetime.UTC)

    def refund(self) -> None:
        self._assert_status(PaymentStatus.COMPLETED)
        self.status = PaymentStatus.REFUNDED
        self.processed_at = datetime.datetime.now(tz=datetime.UTC)

    def _assert_status(self, expected: PaymentStatus) -> None:
        if self.status != expected:
            raise ValueError(f"Expected payment status {expected.value}, got {self.status.value}")
