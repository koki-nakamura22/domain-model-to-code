"""Reservation集約: 予約ライフサイクルの管理。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum

from src.domain.models.shared import Money, new_id


class ReservationStatus(Enum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    NO_SHOW = "NO_SHOW"


class ChildAgeCategory(Enum):
    INFANT = "INFANT"
    SCHOOL_AGE = "SCHOOL_AGE"


CHILD_RATE_FACTORS: dict[ChildAgeCategory, float] = {
    ChildAgeCategory.INFANT: 0.0,
    ChildAgeCategory.SCHOOL_AGE: 0.5,
}


@dataclass(frozen=True)
class StayPeriod:
    check_in_date: datetime.date
    check_out_date: datetime.date

    def __post_init__(self) -> None:
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date must be after check_in_date")

    @property
    def nights(self) -> int:
        return (self.check_out_date - self.check_in_date).days

    @property
    def stay_dates(self) -> list[datetime.date]:
        return [self.check_in_date + datetime.timedelta(days=i) for i in range(self.nights)]


@dataclass(frozen=True)
class GuestCount:
    adults: int
    child_school_age: int = 0
    child_infant: int = 0

    def __post_init__(self) -> None:
        if self.adults <= 0:
            raise ValueError("At least one adult is required")

    @property
    def total(self) -> int:
        return self.adults + self.child_school_age + self.child_infant

    @property
    def billable_count(self) -> int:
        return self.adults + self.child_school_age


@dataclass(frozen=True)
class DailyRate:
    date: datetime.date
    base_amount: Money
    rate_multiplier: float
    occupancy_adjustment: Money
    plan_charge: Money

    @property
    def subtotal(self) -> Money:
        base = self.base_amount.multiply(self.rate_multiplier)
        return base.add(self.occupancy_adjustment).add(self.plan_charge)


@dataclass
class Reservation:
    id: str
    hotel_id: str
    guest_id: str
    room_type_id: str
    rate_plan_id: str
    stay_period: StayPeriod
    guest_count: GuestCount
    status: ReservationStatus
    daily_rates: list[DailyRate] = field(default_factory=lambda: list[DailyRate]())
    total_amount: Money = field(default_factory=Money.zero)
    reservation_number: str | None = None
    assigned_room_id: str | None = None
    expires_at: datetime.datetime | None = None

    @staticmethod
    def hold(
        hotel_id: str,
        guest_id: str,
        room_type_id: str,
        rate_plan_id: str,
        stay_period: StayPeriod,
        guest_count: GuestCount,
        daily_rates: list[DailyRate],
        total_amount: Money,
        expires_at: datetime.datetime,
    ) -> Reservation:
        return Reservation(
            id=new_id(),
            hotel_id=hotel_id,
            guest_id=guest_id,
            room_type_id=room_type_id,
            rate_plan_id=rate_plan_id,
            stay_period=stay_period,
            guest_count=guest_count,
            status=ReservationStatus.HELD,
            daily_rates=daily_rates,
            total_amount=total_amount,
            expires_at=expires_at,
        )

    def confirm(self, reservation_number: str) -> None:
        self._assert_status(ReservationStatus.HELD)
        self.status = ReservationStatus.CONFIRMED
        self.reservation_number = reservation_number
        self.expires_at = None

    def modify(
        self,
        stay_period: StayPeriod,
        guest_count: GuestCount,
        room_type_id: str,
        rate_plan_id: str,
        daily_rates: list[DailyRate],
        total_amount: Money,
    ) -> None:
        self._assert_status(ReservationStatus.CONFIRMED)
        if datetime.date.today() >= self.stay_period.check_in_date:
            raise ValueError("Cannot modify reservation on or after check-in date")
        self.stay_period = stay_period
        self.guest_count = guest_count
        self.room_type_id = room_type_id
        self.rate_plan_id = rate_plan_id
        self.daily_rates = daily_rates
        self.total_amount = total_amount

    def cancel(self) -> None:
        self._assert_status(ReservationStatus.CONFIRMED)
        self.status = ReservationStatus.CANCELLED

    def check_in(self, room_id: str) -> None:
        self._assert_status(ReservationStatus.CONFIRMED)
        self.status = ReservationStatus.CHECKED_IN
        self.assigned_room_id = room_id

    def check_out(self) -> None:
        self._assert_status(ReservationStatus.CHECKED_IN)
        self.status = ReservationStatus.CHECKED_OUT

    def expire(self) -> None:
        self._assert_status(ReservationStatus.HELD)
        self.status = ReservationStatus.EXPIRED

    def mark_no_show(self) -> None:
        self._assert_status(ReservationStatus.CONFIRMED)
        self.status = ReservationStatus.NO_SHOW

    def _assert_status(self, expected: ReservationStatus) -> None:
        if self.status != expected:
            raise ValueError(f"Expected status {expected.value}, got {self.status.value}")
