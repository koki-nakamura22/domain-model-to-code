"""決済処理ユースケース。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.events.events import PaymentCompleted, PaymentFailed
from src.domain.models.payment import Payment, PaymentMethod
from src.domain.models.shared import Money
from src.domain.repositories.payment_repository import PaymentRepository
from src.domain.services.event_publisher import EventPublisher
from src.domain.services.payment_gateway import PaymentGateway


@dataclass
class ProcessPaymentCommand:
    reservation_id: str
    amount: Money
    method: PaymentMethod
    card_info: dict[str, str]


@dataclass
class ProcessPaymentResult:
    payment_id: str
    success: bool
    failure_reason: str | None = None


class ProcessPaymentUseCase:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        payment_gateway: PaymentGateway,
        event_publisher: EventPublisher,
    ) -> None:
        self._payment_repo = payment_repo
        self._payment_gateway = payment_gateway
        self._event_publisher = event_publisher

    async def execute(self, command: ProcessPaymentCommand) -> ProcessPaymentResult:
        payment = Payment.create(
            reservation_id=command.reservation_id,
            amount=command.amount,
            method=command.method,
        )

        result = await self._payment_gateway.process(
            amount=command.amount,
            method=command.method.value,
            card_info=command.card_info,
        )

        now = datetime.datetime.now(tz=datetime.UTC)

        if result.success:
            payment.complete()
            await self._payment_repo.save(payment)
            await self._event_publisher.publish(
                PaymentCompleted(
                    occurred_at=now,
                    payment_id=payment.id,
                    reservation_id=command.reservation_id,
                    amount=command.amount,
                )
            )
            return ProcessPaymentResult(payment_id=payment.id, success=True)
        else:
            payment.fail()
            await self._payment_repo.save(payment)
            await self._event_publisher.publish(
                PaymentFailed(
                    occurred_at=now,
                    payment_id=payment.id,
                    reservation_id=command.reservation_id,
                    amount=command.amount,
                    failure_reason=result.failure_reason or "Unknown error",
                )
            )
            return ProcessPaymentResult(payment_id=payment.id, success=False, failure_reason=result.failure_reason)
