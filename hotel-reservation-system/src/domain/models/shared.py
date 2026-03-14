"""SharedKernel: 共有値オブジェクト。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum


class Currency(Enum):
    JPY = "JPY"
    USD = "USD"


@dataclass(frozen=True)
class Money:
    amount: int
    currency: Currency = Currency.JPY

    def add(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: float) -> Money:
        return Money(amount=round(self.amount * factor), currency=self.currency)

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")

    @staticmethod
    def zero(currency: Currency = Currency.JPY) -> Money:
        return Money(amount=0, currency=currency)


def new_id() -> str:
    return str(uuid.uuid4())
