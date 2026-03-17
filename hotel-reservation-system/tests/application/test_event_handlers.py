"""イベントハンドラのテスト。"""

import datetime

import pytest

from src.application.event_handlers.no_show_detected_notification_handler import NoShowDetectedNotificationHandler
from src.application.event_handlers.payment_completed_handler import PaymentCompletedHandler
from src.application.event_handlers.payment_failed_handler import PaymentFailedHandler
from src.application.event_handlers.payment_failed_notification_handler import PaymentFailedNotificationHandler
from src.application.event_handlers.reservation_cancelled_notification_handler import (
    ReservationCancelledNotificationHandler,
)
from src.application.event_handlers.reservation_cancelled_refund_handler import ReservationCancelledRefundHandler
from src.application.event_handlers.reservation_confirmed_notification_handler import (
    ReservationConfirmedNotificationHandler,
)
from src.application.event_handlers.reservation_modified_notification_handler import (
    ReservationModifiedNotificationHandler,
)
from src.application.event_handlers.reservation_modified_payment_handler import ReservationModifiedPaymentHandler
from src.domain.events.events import (
    DomainEvent,
    NoShowDetected,
    PaymentCompleted,
    PaymentFailed,
    ReservationCancelled,
    ReservationConfirmed,
    ReservationExpired,
    ReservationModified,
)
from src.domain.models.reservation import GuestCount, Reservation, ReservationStatus, StayPeriod
from src.domain.models.shared import Money
from src.domain.services.payment_gateway import PaymentResult

# === テスト用スタブ ===


class SpyEventPublisher:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


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


class SpyPaymentGateway:
    def __init__(self) -> None:
        self.process_calls: list[tuple[Money, str, dict[str, str]]] = []
        self.refund_calls: list[tuple[Money, str]] = []

    async def process(self, amount: Money, method: str, card_info: dict[str, str]) -> PaymentResult:
        self.process_calls.append((amount, method, card_info))
        return PaymentResult(success=True)

    async def refund(self, amount: Money, original_transaction_id: str) -> PaymentResult:
        self.refund_calls.append((amount, original_transaction_id))
        return PaymentResult(success=True)


class SpyNotificationService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def send_reservation_confirmed(
        self, guest_id: str, reservation_number: str, stay_period: StayPeriod, total_amount: Money
    ) -> None:
        self.calls.append(("confirmed", {"guest_id": guest_id, "reservation_number": reservation_number}))

    async def send_reservation_modified(
        self,
        guest_id: str,
        reservation_number: str,
        new_stay_period: StayPeriod,
        new_total_amount: Money,
        amount_difference: Money,
    ) -> None:
        self.calls.append(("modified", {"guest_id": guest_id, "reservation_number": reservation_number}))

    async def send_reservation_cancelled(
        self, guest_id: str, reservation_number: str, cancellation_fee: Money, refund_amount: Money
    ) -> None:
        self.calls.append(("cancelled", {"guest_id": guest_id, "reservation_number": reservation_number}))

    async def send_no_show_detected(self, guest_id: str, reservation_number: str, total_amount: Money) -> None:
        self.calls.append(("no_show", {"guest_id": guest_id, "reservation_number": reservation_number}))

    async def send_payment_failed(self, reservation_id: str, reason: str) -> None:
        self.calls.append(("payment_failed", {"reservation_id": reservation_id, "reason": reason}))


# === ヘルパー ===

NOW = datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC)
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
        expires_at=NOW + datetime.timedelta(minutes=15),
    )


# === PaymentCompletedHandler ===


@pytest.mark.asyncio
async def test_payment_completed__reservation_confirmed() -> None:
    repo = InMemoryReservationRepository()
    reservation = _held_reservation()
    await repo.save(reservation)

    event_publisher = SpyEventPublisher()
    handler = PaymentCompletedHandler(reservation_repo=repo, event_publisher=event_publisher)

    event = PaymentCompleted(occurred_at=NOW, payment_id="pay-1", reservation_id="res-1", amount=Money(amount=20000))
    await handler.handle(event)

    saved = await repo.find_by_id("res-1")
    assert saved is not None
    assert saved.status == ReservationStatus.CONFIRMED
    assert len(event_publisher.events) == 1
    assert isinstance(event_publisher.events[0], ReservationConfirmed)


# === PaymentFailedHandler ===


@pytest.mark.asyncio
async def test_payment_failed__reservation_expired() -> None:
    repo = InMemoryReservationRepository()
    reservation = _held_reservation()
    await repo.save(reservation)

    event_publisher = SpyEventPublisher()
    handler = PaymentFailedHandler(reservation_repo=repo, event_publisher=event_publisher)

    event = PaymentFailed(
        occurred_at=NOW,
        payment_id="pay-1",
        reservation_id="res-1",
        amount=Money(amount=20000),
        failure_reason="declined",
    )
    await handler.handle(event)

    saved = await repo.find_by_id("res-1")
    assert saved is not None
    assert saved.status == ReservationStatus.EXPIRED
    assert len(event_publisher.events) == 1
    assert isinstance(event_publisher.events[0], ReservationExpired)


@pytest.mark.asyncio
async def test_payment_failed_reservation_not_found__no_error() -> None:
    repo = InMemoryReservationRepository()
    event_publisher = SpyEventPublisher()
    handler = PaymentFailedHandler(reservation_repo=repo, event_publisher=event_publisher)

    event = PaymentFailed(
        occurred_at=NOW,
        payment_id="pay-1",
        reservation_id="nonexistent",
        amount=Money(amount=20000),
        failure_reason="declined",
    )
    await handler.handle(event)

    assert len(event_publisher.events) == 0


# === ReservationModifiedPaymentHandler ===


@pytest.mark.asyncio
async def test_reservation_modified_surcharge__additional_payment_processed() -> None:
    gateway = SpyPaymentGateway()
    handler = ReservationModifiedPaymentHandler(payment_gateway=gateway)

    event = ReservationModified(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        previous_stay_period=STAY,
        new_stay_period=StayPeriod(check_in_date=datetime.date(2026, 4, 10), check_out_date=datetime.date(2026, 4, 13)),
        previous_total_amount=Money(amount=20000),
        new_total_amount=Money(amount=30000),
        amount_difference=Money(amount=10000),
    )
    await handler.handle(event)

    assert len(gateway.process_calls) == 1
    assert gateway.process_calls[0][0] == Money(amount=10000)
    assert len(gateway.refund_calls) == 0


@pytest.mark.asyncio
async def test_reservation_modified_discount__refund_processed() -> None:
    gateway = SpyPaymentGateway()
    handler = ReservationModifiedPaymentHandler(payment_gateway=gateway)

    event = ReservationModified(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        previous_stay_period=STAY,
        new_stay_period=StayPeriod(check_in_date=datetime.date(2026, 4, 10), check_out_date=datetime.date(2026, 4, 11)),
        previous_total_amount=Money(amount=20000),
        new_total_amount=Money(amount=10000),
        amount_difference=Money(amount=-10000),
    )
    await handler.handle(event)

    assert len(gateway.refund_calls) == 1
    assert gateway.refund_calls[0][0] == Money(amount=10000)
    assert len(gateway.process_calls) == 0


@pytest.mark.asyncio
async def test_reservation_modified_no_difference__no_payment_action() -> None:
    gateway = SpyPaymentGateway()
    handler = ReservationModifiedPaymentHandler(payment_gateway=gateway)

    event = ReservationModified(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        previous_stay_period=STAY,
        new_stay_period=STAY,
        previous_total_amount=Money(amount=20000),
        new_total_amount=Money(amount=20000),
        amount_difference=Money(amount=0),
    )
    await handler.handle(event)

    assert len(gateway.process_calls) == 0
    assert len(gateway.refund_calls) == 0


# === ReservationCancelledRefundHandler ===


@pytest.mark.asyncio
async def test_reservation_cancelled_with_refund__refund_processed() -> None:
    gateway = SpyPaymentGateway()
    handler = ReservationCancelledRefundHandler(payment_gateway=gateway)

    event = ReservationCancelled(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        cancellation_fee=Money(amount=5000),
        refund_amount=Money(amount=15000),
    )
    await handler.handle(event)

    assert len(gateway.refund_calls) == 1
    assert gateway.refund_calls[0][0] == Money(amount=15000)


@pytest.mark.asyncio
async def test_reservation_cancelled_no_refund__no_refund_processed() -> None:
    gateway = SpyPaymentGateway()
    handler = ReservationCancelledRefundHandler(payment_gateway=gateway)

    event = ReservationCancelled(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        cancellation_fee=Money(amount=20000),
        refund_amount=Money(amount=0),
    )
    await handler.handle(event)

    assert len(gateway.refund_calls) == 0


# === 通知系ハンドラ ===


@pytest.mark.asyncio
async def test_reservation_confirmed__confirmation_notification_sent() -> None:
    ns = SpyNotificationService()
    handler = ReservationConfirmedNotificationHandler(notification_service=ns)

    event = ReservationConfirmed(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        stay_period=STAY,
        total_amount=Money(amount=20000),
        payment_id="pay-1",
    )
    await handler.handle(event)

    assert len(ns.calls) == 1
    assert ns.calls[0][0] == "confirmed"


@pytest.mark.asyncio
async def test_reservation_modified__modification_notification_sent() -> None:
    ns = SpyNotificationService()
    handler = ReservationModifiedNotificationHandler(notification_service=ns)

    event = ReservationModified(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        previous_stay_period=STAY,
        new_stay_period=STAY,
        previous_total_amount=Money(amount=20000),
        new_total_amount=Money(amount=20000),
        amount_difference=Money(amount=0),
    )
    await handler.handle(event)

    assert len(ns.calls) == 1
    assert ns.calls[0][0] == "modified"


@pytest.mark.asyncio
async def test_reservation_cancelled__cancellation_notification_sent() -> None:
    ns = SpyNotificationService()
    handler = ReservationCancelledNotificationHandler(notification_service=ns)

    event = ReservationCancelled(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        cancellation_fee=Money(amount=5000),
        refund_amount=Money(amount=15000),
    )
    await handler.handle(event)

    assert len(ns.calls) == 1
    assert ns.calls[0][0] == "cancelled"


@pytest.mark.asyncio
async def test_no_show_detected__no_show_notification_sent() -> None:
    ns = SpyNotificationService()
    handler = NoShowDetectedNotificationHandler(notification_service=ns)

    event = NoShowDetected(
        occurred_at=NOW,
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        total_amount=Money(amount=20000),
    )
    await handler.handle(event)

    assert len(ns.calls) == 1
    assert ns.calls[0][0] == "no_show"


@pytest.mark.asyncio
async def test_payment_failed__payment_failed_notification_sent() -> None:
    ns = SpyNotificationService()
    handler = PaymentFailedNotificationHandler(notification_service=ns)

    event = PaymentFailed(
        occurred_at=NOW,
        payment_id="pay-1",
        reservation_id="res-1",
        amount=Money(amount=20000),
        failure_reason="Card declined",
    )
    await handler.handle(event)

    assert len(ns.calls) == 1
    assert ns.calls[0][0] == "payment_failed"
    assert ns.calls[0][1]["reason"] == "Card declined"
