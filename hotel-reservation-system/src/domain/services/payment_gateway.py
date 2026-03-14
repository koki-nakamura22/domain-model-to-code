"""決済ゲートウェイProtocol。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.models.shared import Money


@dataclass(frozen=True)
class PaymentResult:
    success: bool
    failure_reason: str | None = None


class PaymentGateway(Protocol):
    async def process(self, amount: Money, method: str, card_info: dict[str, str]) -> PaymentResult: ...
    async def refund(self, amount: Money, original_transaction_id: str) -> PaymentResult: ...
