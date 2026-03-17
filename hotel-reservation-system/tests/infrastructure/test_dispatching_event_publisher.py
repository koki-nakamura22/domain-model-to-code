"""DispatchingEventPublisher のテスト。"""

import datetime

import pytest

from src.domain.events.events import DomainEvent, PaymentCompleted, ReservationConfirmed
from src.domain.models.reservation import StayPeriod
from src.domain.models.shared import Money
from src.infrastructure.event_publisher import DispatchingEventPublisher


@pytest.mark.asyncio
async def test_subscribed_handler__handler_called() -> None:
    publisher = DispatchingEventPublisher()
    received: list[DomainEvent] = []

    async def handler(event: PaymentCompleted) -> None:
        received.append(event)

    publisher.subscribe(PaymentCompleted, handler)

    event = PaymentCompleted(
        occurred_at=datetime.datetime(2026, 4, 1, tzinfo=datetime.UTC),
        payment_id="pay-1",
        reservation_id="res-1",
        amount=Money(amount=10000),
    )
    await publisher.publish(event)

    assert len(received) == 1
    assert received[0] is event


@pytest.mark.asyncio
async def test_multiple_handlers_for_same_event__all_handlers_called() -> None:
    publisher = DispatchingEventPublisher()
    received_a: list[DomainEvent] = []
    received_b: list[DomainEvent] = []

    async def handler_a(event: PaymentCompleted) -> None:
        received_a.append(event)

    async def handler_b(event: PaymentCompleted) -> None:
        received_b.append(event)

    publisher.subscribe(PaymentCompleted, handler_a)
    publisher.subscribe(PaymentCompleted, handler_b)

    event = PaymentCompleted(
        occurred_at=datetime.datetime(2026, 4, 1, tzinfo=datetime.UTC),
        payment_id="pay-1",
        reservation_id="res-1",
        amount=Money(amount=10000),
    )
    await publisher.publish(event)

    assert len(received_a) == 1
    assert len(received_b) == 1


@pytest.mark.asyncio
async def test_unsubscribed_event_type__no_handler_called() -> None:
    publisher = DispatchingEventPublisher()
    received: list[DomainEvent] = []

    async def handler(event: PaymentCompleted) -> None:
        received.append(event)

    publisher.subscribe(PaymentCompleted, handler)

    event = ReservationConfirmed(
        occurred_at=datetime.datetime(2026, 4, 1, tzinfo=datetime.UTC),
        reservation_id="res-1",
        reservation_number="R-001",
        hotel_id="hotel-1",
        guest_id="guest-1",
        stay_period=StayPeriod(check_in_date=datetime.date(2026, 4, 10), check_out_date=datetime.date(2026, 4, 12)),
        total_amount=Money(amount=20000),
        payment_id="pay-1",
    )
    await publisher.publish(event)

    assert len(received) == 0
