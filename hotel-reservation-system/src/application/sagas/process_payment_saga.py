"""決済→予約確定 Saga。

外部決済サービスとローカルDBの整合性を補償処理で担保する。

正常フロー:
  1. 外部決済サービスに課金
  2. 予約を確定（HELD → CONFIRMED）
  3. PaymentCompleted + ReservationConfirmed イベント発行

異常フロー:
  - Step 1 失敗 → 予約を失効、PaymentFailed 発行
  - Step 2 失敗 → Step 1 の補償（返金）を実行、例外を再送出
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass

from src.domain.events.events import (
    PaymentCompleted,
    PaymentFailed,
    ReservationConfirmed,
    ReservationExpired,
)
from src.domain.models.payment import Payment, PaymentMethod
from src.domain.models.shared import Money
from src.domain.repositories.payment_repository import PaymentRepository
from src.domain.repositories.reservation_repository import ReservationRepository
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


class ProcessPaymentSaga:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        payment_gateway: PaymentGateway,
        reservation_repo: ReservationRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._payment_repo = payment_repo
        self._payment_gateway = payment_gateway
        self._reservation_repo = reservation_repo
        self._event_publisher = event_publisher

    async def execute(self, command: ProcessPaymentCommand) -> ProcessPaymentResult:
        now = datetime.datetime.now(tz=datetime.UTC)

        payment = Payment.create(
            reservation_id=command.reservation_id,
            amount=command.amount,
            method=command.method,
        )

        # === Step 1: 外部決済サービスに課金 ===
        gateway_result = await self._payment_gateway.process(
            amount=command.amount,
            method=command.method.value,
            card_info=command.card_info,
        )

        if not gateway_result.success:
            return await self._handle_payment_failure(
                payment, command, now, gateway_result.failure_reason or "Unknown error"
            )

        # === Step 2: 予約確定（ローカルDB） ===
        payment.complete()
        await self._payment_repo.save(payment)

        try:
            reservation = await self._reservation_repo.find_by_id(command.reservation_id)
            if not reservation:
                raise ValueError(f"Reservation not found: {command.reservation_id}")

            reservation_number = f"R-{uuid.uuid4().hex[:8].upper()}"
            reservation.confirm(reservation_number)
            await self._reservation_repo.save(reservation)
        except Exception:
            # === 補償: Step 1 の返金 ===
            await self._payment_gateway.refund(
                amount=command.amount,
                original_transaction_id=payment.id,
            )
            raise

        # === 全ステップ成功: イベント発行 ===
        await self._event_publisher.publish(
            PaymentCompleted(
                occurred_at=now,
                payment_id=payment.id,
                reservation_id=command.reservation_id,
                amount=command.amount,
            )
        )
        await self._event_publisher.publish(
            ReservationConfirmed(
                occurred_at=now,
                reservation_id=reservation.id,
                reservation_number=reservation_number,
                hotel_id=reservation.hotel_id,
                guest_id=reservation.guest_id,
                stay_period=reservation.stay_period,
                total_amount=reservation.total_amount,
                payment_id=payment.id,
            )
        )

        return ProcessPaymentResult(payment_id=payment.id, success=True)

    async def _handle_payment_failure(
        self,
        payment: Payment,
        command: ProcessPaymentCommand,
        now: datetime.datetime,
        failure_reason: str,
    ) -> ProcessPaymentResult:
        """決済失敗時: 予約を失効し、PaymentFailed イベントを発行する。"""
        payment.fail()
        await self._payment_repo.save(payment)

        reservation = await self._reservation_repo.find_by_id(command.reservation_id)
        if reservation:
            reservation.expire()
            await self._reservation_repo.save(reservation)
            await self._event_publisher.publish(
                ReservationExpired(
                    occurred_at=now,
                    reservation_id=reservation.id,
                    hotel_id=reservation.hotel_id,
                    room_type_id=reservation.room_type_id,
                    stay_period=reservation.stay_period,
                )
            )

        await self._event_publisher.publish(
            PaymentFailed(
                occurred_at=now,
                payment_id=payment.id,
                reservation_id=command.reservation_id,
                amount=command.amount,
                failure_reason=failure_reason,
            )
        )

        return ProcessPaymentResult(
            payment_id=payment.id,
            success=False,
            failure_reason=failure_reason,
        )
