"""料金計算ドメインサービス。"""

from __future__ import annotations

from src.domain.models.hotel import DayType, Hotel
from src.domain.models.rate_plan import RatePlan
from src.domain.models.reservation import (
    CHILD_RATE_FACTORS,
    ChildAgeCategory,
    DailyRate,
    GuestCount,
    StayPeriod,
)
from src.domain.models.room_type import RoomType
from src.domain.models.shared import Money


def _get_day_type(date_weekday: int) -> DayType:
    if date_weekday == 4:
        return DayType.FRIDAY
    if date_weekday == 5:
        return DayType.SATURDAY_OR_HOLIDAY_EVE
    return DayType.WEEKDAY


def calculate_daily_rates(
    hotel: Hotel,
    room_type: RoomType,
    rate_plan: RatePlan,
    stay_period: StayPeriod,
    guest_count: GuestCount,
) -> list[DailyRate]:
    rates: list[DailyRate] = []

    occupancy_adj = room_type.calculate_occupancy_adjustment(guest_count.adults)

    child_school_charge = rate_plan.additional_charge_per_person.multiply(
        CHILD_RATE_FACTORS[ChildAgeCategory.SCHOOL_AGE] * guest_count.child_school_age
    )

    plan_charge = rate_plan.additional_charge_per_person.multiply(float(guest_count.adults)).add(child_school_charge)

    for date in stay_period.stay_dates:
        season = hotel.find_season(date)
        season_type = season.season_type if season else hotel.seasons[0].season_type if hotel.seasons else None

        day_type = _get_day_type(date.weekday())

        multiplier = hotel.get_rate_multiplier(season_type, day_type) if season_type else 1.0

        daily_rate = DailyRate(
            date=date,
            base_amount=room_type.base_rate,
            rate_multiplier=multiplier,
            occupancy_adjustment=occupancy_adj,
            plan_charge=plan_charge,
        )
        rates.append(daily_rate)

    return rates


def calculate_total_amount(daily_rates: list[DailyRate], hotel: Hotel) -> Money:
    if not daily_rates:
        return Money.zero()

    subtotal = Money.zero()
    for rate in daily_rates:
        subtotal = subtotal.add(rate.subtotal)

    discount_rate = hotel.length_of_stay_discount.get_discount_rate(len(daily_rates))
    if discount_rate > 0:
        discount = subtotal.multiply(discount_rate)
        subtotal = subtotal.subtract(discount)

    return subtotal
