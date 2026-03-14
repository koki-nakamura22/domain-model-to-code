"""ドメインイベント定義。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.models.reservation import GuestCount, StayPeriod
from src.domain.models.room import RoomStatus
from src.domain.models.shared import Money


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime.datetime


@dataclass(frozen=True)
class ReservationHeld(DomainEvent):
    reservation_id: str
    hotel_id: str
    guest_id: str
    room_type_id: str
    rate_plan_id: str
    stay_period: StayPeriod
    guest_count: GuestCount
    total_amount: Money
    expires_at: datetime.datetime


@dataclass(frozen=True)
class ReservationExpired(DomainEvent):
    reservation_id: str
    hotel_id: str
    room_type_id: str
    stay_period: StayPeriod


@dataclass(frozen=True)
class ReservationConfirmed(DomainEvent):
    reservation_id: str
    reservation_number: str
    hotel_id: str
    guest_id: str
    stay_period: StayPeriod
    total_amount: Money
    payment_id: str


@dataclass(frozen=True)
class ReservationModified(DomainEvent):
    reservation_id: str
    reservation_number: str
    hotel_id: str
    guest_id: str
    previous_stay_period: StayPeriod
    new_stay_period: StayPeriod
    previous_total_amount: Money
    new_total_amount: Money
    amount_difference: Money


@dataclass(frozen=True)
class ReservationCancelled(DomainEvent):
    reservation_id: str
    reservation_number: str
    hotel_id: str
    guest_id: str
    cancellation_fee: Money
    refund_amount: Money


@dataclass(frozen=True)
class GuestCheckedIn(DomainEvent):
    reservation_id: str
    reservation_number: str
    hotel_id: str
    guest_id: str
    room_id: str
    room_number: str


@dataclass(frozen=True)
class GuestCheckedOut(DomainEvent):
    reservation_id: str
    reservation_number: str
    hotel_id: str
    guest_id: str
    room_id: str


@dataclass(frozen=True)
class NoShowDetected(DomainEvent):
    reservation_id: str
    reservation_number: str
    hotel_id: str
    guest_id: str
    total_amount: Money


@dataclass(frozen=True)
class PaymentCompleted(DomainEvent):
    payment_id: str
    reservation_id: str
    amount: Money


@dataclass(frozen=True)
class PaymentFailed(DomainEvent):
    payment_id: str
    reservation_id: str
    amount: Money
    failure_reason: str


@dataclass(frozen=True)
class RoomStatusChanged(DomainEvent):
    room_id: str
    hotel_id: str
    room_number: str
    previous_status: RoomStatus
    new_status: RoomStatus
