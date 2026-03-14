"""Hotel集約: ホテルの基本情報、シーズン、料金係数、キャンセルポリシー、連泊割引。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum

from src.domain.models.shared import Money, new_id


class SeasonType(Enum):
    OFF = "OFF"
    REGULAR = "REGULAR"
    HIGH = "HIGH"
    PEAK = "PEAK"


class DayType(Enum):
    WEEKDAY = "WEEKDAY"
    FRIDAY = "FRIDAY"
    SATURDAY_OR_HOLIDAY_EVE = "SATURDAY_OR_HOLIDAY_EVE"


@dataclass(frozen=True)
class Season:
    season_type: SeasonType
    start_date: datetime.date
    end_date: datetime.date

    def contains(self, date: datetime.date) -> bool:
        return self.start_date <= date <= self.end_date


@dataclass(frozen=True)
class RateMultiplier:
    season_type: SeasonType
    day_type: DayType
    multiplier: float


@dataclass(frozen=True)
class CancellationRule:
    days_before_check_in: int
    fee_rate: float


@dataclass(frozen=True)
class CancellationPolicy:
    rules: list[CancellationRule]

    def calculate_fee_rate(self, check_in_date: datetime.date, cancel_date: datetime.date) -> float:
        days_before = (check_in_date - cancel_date).days
        sorted_rules = sorted(self.rules, key=lambda r: r.days_before_check_in)
        matched_rate = 0.0
        for rule in sorted_rules:
            if days_before <= rule.days_before_check_in:
                matched_rate = rule.fee_rate
                break
        return matched_rate


@dataclass(frozen=True)
class DiscountTier:
    min_nights: int
    discount_rate: float


@dataclass(frozen=True)
class LengthOfStayDiscount:
    tiers: list[DiscountTier]

    def get_discount_rate(self, nights: int) -> float:
        applicable = [t for t in self.tiers if nights >= t.min_nights]
        if not applicable:
            return 0.0
        return max(t.discount_rate for t in applicable)


@dataclass(frozen=True)
class CheckInOutPolicy:
    check_in_time: datetime.time
    check_out_time: datetime.time


@dataclass
class Hotel:
    id: str
    name: str
    check_in_out_policy: CheckInOutPolicy
    seasons: list[Season] = field(default_factory=lambda: list[Season]())
    rate_multipliers: list[RateMultiplier] = field(default_factory=lambda: list[RateMultiplier]())
    cancellation_policy: CancellationPolicy = field(default_factory=lambda: CancellationPolicy(rules=[]))
    length_of_stay_discount: LengthOfStayDiscount = field(default_factory=lambda: LengthOfStayDiscount(tiers=[]))

    @staticmethod
    def create(
        name: str,
        check_in_out_policy: CheckInOutPolicy,
        seasons: list[Season] | None = None,
        rate_multipliers: list[RateMultiplier] | None = None,
        cancellation_policy: CancellationPolicy | None = None,
        length_of_stay_discount: LengthOfStayDiscount | None = None,
    ) -> Hotel:
        return Hotel(
            id=new_id(),
            name=name,
            check_in_out_policy=check_in_out_policy,
            seasons=seasons or [],
            rate_multipliers=rate_multipliers or [],
            cancellation_policy=cancellation_policy or CancellationPolicy(rules=[]),
            length_of_stay_discount=length_of_stay_discount or LengthOfStayDiscount(tiers=[]),
        )

    def find_season(self, date: datetime.date) -> Season | None:
        for season in self.seasons:
            if season.contains(date):
                return season
        return None

    def get_rate_multiplier(self, season_type: SeasonType, day_type: DayType) -> float:
        for rm in self.rate_multipliers:
            if rm.season_type == season_type and rm.day_type == day_type:
                return rm.multiplier
        return 1.0

    def calculate_cancellation_fee(
        self, total_amount: Money, check_in_date: datetime.date, cancel_date: datetime.date
    ) -> Money:
        fee_rate = self.cancellation_policy.calculate_fee_rate(check_in_date, cancel_date)
        return total_amount.multiply(fee_rate)
