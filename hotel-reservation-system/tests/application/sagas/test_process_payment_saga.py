"""決済→予約確定 Saga のテスト。"""

import datetime

import pytest

from src.application.sagas.process_payment_saga import (
    ProcessPaymentCommand,
    ProcessPaymentSaga,
)
from src.domain.events.events import (
    DomainEvent,
    PaymentCompleted,
    PaymentFailed,
    ReservationConfirmed,
    ReservationExpired,
)
from src.domain.models.payment import Payment, PaymentMethod
from src.domain.models.reservation import GuestCount, Reservation, ReservationStatus, StayPeriod
from src.domain.models.shared import Money
from src.domain.services.payment_gateway import PaymentResult

# === テスト用スタブ ===


class SpyEventPublisher:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


class InMemoryPaymentRepository:
    def __init__(self) -> None:
        self._data: dict[str, Payment] = {}

    async def find_by_id(self, payment_id: str) -> Payment | None:
        return self._data.get(payment_id)

    async def find_by_reservation_id(self, reservation_id: str) -> list[Payment]:
        return [p for p in self._data.values() if p.reservation_id == reservation_id]

    async def save(self, payment: Payment) -> None:
        self._data[payment.id] = payment


class InMemoryReservationRepository:
    def __init__(self) -> None:
        self._data: dict[str, Reservation] = {}

    async def find_by_id(self, reservation_id: str) -> Reservation | None:
        return self._data.get(reservation_id)

    async def save(self, reservation: Reservation) -> None:
        self._data[reservation.id] = reservation

    async def find_expired_held(self, now: datetime.datetime) -> list[Reservation]:
        return [
            r
            for r in self._data.values()
            if r.status == ReservationStatus.HELD and r.expires_at is not None and r.expires_at <= now
        ]

    async def find_no_shows(self, check_in_date: datetime.date) -> list[Reservation]:
        return [
            r
            for r in self._data.values()
            if r.status == ReservationStatus.CONFIRMED and r.stay_period.check_in_date == check_in_date
        ]

    async def find_by_hotel(
        self,
        hotel_id: str,
        status: ReservationStatus | None = None,
        check_in_from: datetime.date | None = None,
        check_in_to: datetime.date | None = None,
    ) -> list[Reservation]:
        return [r for r in self._data.values() if r.hotel_id == hotel_id]

    async def count_held_and_confirmed(
        self, hotel_id: str, room_type_id: str, check_in: datetime.date, check_out: datetime.date
    ) -> int:
        return 0


class StubPaymentGateway:
    def __init__(self, *, succeed: bool = True) -> None:
        self._succeed = succeed
        self.refund_calls: list[tuple[Money, str]] = []

    async def process(self, amount: Money, method: str, card_info: dict[str, str]) -> PaymentResult:
        if self._succeed:
            return PaymentResult(success=True)
        return PaymentResult(success=False, failure_reason="Card declined")

    async def refund(self, amount: Money, original_transaction_id: str) -> PaymentResult:
        self.refund_calls.append((amount, original_transaction_id))
        return PaymentResult(success=True)


# === ヘルパー ===

STAY = StayPeriod(check_in_date=datetime.date(2026, 4, 10), check_out_date=datetime.date(2026, 4, 12))


def _held_reservation(reservation_id: str = "res-1") -> Reservation:
    return Reservation(
        id=reservation_id,
        hotel_id="hotel-1",
        guest_id="guest-1",
        room_type_id="rt-1",
        rate_plan_id="rp-1",
        stay_period=STAY,
        guest_count=GuestCount(adults=2),
        status=ReservationStatus.HELD,
        total_amount=Money(amount=20000),
        expires_at=datetime.datetime(2026, 4, 1, 12, 15, tzinfo=datetime.UTC),
    )


def _command(reservation_id: str = "res-1") -> ProcessPaymentCommand:
    return ProcessPaymentCommand(
        reservation_id=reservation_id,
        amount=Money(amount=20000),
        method=PaymentMethod.CREDIT_CARD,
        card_info={"number": "4111111111111111"},
    )


# === 正常フロー ===


@pytest.mark.asyncio
async def test_payment_and_confirm_succeed__reservation_confirmed_with_events() -> None:
    reservation_repo = InMemoryReservationRepository()
    await reservation_repo.save(_held_reservation())
    payment_repo = InMemoryPaymentRepository()
    gateway = StubPaymentGateway(succeed=True)
    event_publisher = SpyEventPublisher()

    saga = ProcessPaymentSaga(
        payment_repo=payment_repo,
        payment_gateway=gateway,
        reservation_repo=reservation_repo,
        event_publisher=event_publisher,
    )
    result = await saga.execute(_command())

    assert result.success is True
    reservation = await reservation_repo.find_by_id("res-1")
    assert reservation is not None
    assert reservation.status == ReservationStatus.CONFIRMED
    assert reservation.reservation_number is not None

    event_types = [type(e) for e in event_publisher.events]
    assert PaymentCompleted in event_types
    assert ReservationConfirmed in event_types


# === 決済失敗 ===


@pytest.mark.asyncio
async def test_payment_declined__reservation_expired() -> None:
    reservation_repo = InMemoryReservationRepository()
    await reservation_repo.save(_held_reservation())
    payment_repo = InMemoryPaymentRepository()
    gateway = StubPaymentGateway(succeed=False)
    event_publisher = SpyEventPublisher()

    saga = ProcessPaymentSaga(
        payment_repo=payment_repo,
        payment_gateway=gateway,
        reservation_repo=reservation_repo,
        event_publisher=event_publisher,
    )
    result = await saga.execute(_command())

    assert result.success is False
    assert result.failure_reason == "Card declined"
    reservation = await reservation_repo.find_by_id("res-1")
    assert reservation is not None
    assert reservation.status == ReservationStatus.EXPIRED

    event_types = [type(e) for e in event_publisher.events]
    assert ReservationExpired in event_types
    assert PaymentFailed in event_types


# === 予約確定失敗 → 補償（返金） ===


@pytest.mark.asyncio
async def test_confirm_fails__payment_refunded() -> None:
    reservation_repo = InMemoryReservationRepository()
    # 予約が存在しない → confirm で ValueError
    payment_repo = InMemoryPaymentRepository()
    gateway = StubPaymentGateway(succeed=True)
    event_publisher = SpyEventPublisher()

    saga = ProcessPaymentSaga(
        payment_repo=payment_repo,
        payment_gateway=gateway,
        reservation_repo=reservation_repo,
        event_publisher=event_publisher,
    )

    with pytest.raises(ValueError, match="Reservation not found"):
        await saga.execute(_command())

    # 補償: 外部決済サービスへの返金が呼ばれた
    assert len(gateway.refund_calls) == 1
    assert gateway.refund_calls[0][0] == Money(amount=20000)

    # イベントは発行されていない（全ステップ成功前なので）
    assert len(event_publisher.events) == 0
