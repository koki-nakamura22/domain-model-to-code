"""モック決済ゲートウェイ。"""

from __future__ import annotations

from src.domain.models.shared import Money
from src.domain.services.payment_gateway import PaymentResult


class MockPaymentGateway:
    def __init__(self, always_succeed: bool = True) -> None:
        self._always_succeed = always_succeed

    async def process(self, amount: Money, method: str, card_info: dict[str, str]) -> PaymentResult:
        if self._always_succeed:
            return PaymentResult(success=True)
        return PaymentResult(success=False, failure_reason="Mock payment declined")

    async def refund(self, amount: Money, original_transaction_id: str) -> PaymentResult:
        return PaymentResult(success=True)
