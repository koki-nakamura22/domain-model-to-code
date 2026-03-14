"""料金計算ドメインサービスのテスト。"""

import datetime

from src.domain.models.hotel import (
    CheckInOutPolicy,
    DayType,
    DiscountTier,
    Hotel,
    LengthOfStayDiscount,
    RateMultiplier,
    Season,
    SeasonType,
)
from src.domain.models.rate_plan import RatePlan, RatePlanType
from src.domain.models.reservation import GuestCount, StayPeriod
from src.domain.models.room_type import Occupancy, OccupancyAdjustment, RoomType
from src.domain.models.shared import Money
from src.domain.services.pricing_service import calculate_daily_rates, calculate_total_amount


def _make_hotel() -> Hotel:
    return Hotel(
        id="hotel-1",
        name="テストホテル",
        check_in_out_policy=CheckInOutPolicy(
            check_in_time=datetime.time(15, 0),
            check_out_time=datetime.time(10, 0),
        ),
        seasons=[
            Season(SeasonType.REGULAR, datetime.date(2026, 4, 1), datetime.date(2026, 6, 30)),
            Season(SeasonType.HIGH, datetime.date(2026, 7, 1), datetime.date(2026, 8, 31)),
        ],
        rate_multipliers=[
            RateMultiplier(SeasonType.REGULAR, DayType.WEEKDAY, 1.0),
            RateMultiplier(SeasonType.REGULAR, DayType.FRIDAY, 1.1),
            RateMultiplier(SeasonType.REGULAR, DayType.SATURDAY_OR_HOLIDAY_EVE, 1.3),
            RateMultiplier(SeasonType.HIGH, DayType.WEEKDAY, 1.2),
            RateMultiplier(SeasonType.HIGH, DayType.SATURDAY_OR_HOLIDAY_EVE, 1.5),
        ],
        length_of_stay_discount=LengthOfStayDiscount(
            tiers=[
                DiscountTier(min_nights=3, discount_rate=0.05),
                DiscountTier(min_nights=7, discount_rate=0.10),
            ]
        ),
    )


def _make_room_type() -> RoomType:
    return RoomType(
        id="rt-1",
        hotel_id="hotel-1",
        name="ツイン",
        occupancy=Occupancy(standard_count=2, max_count=4),
        base_rate=Money(amount=10000),
        occupancy_adjustments=[
            OccupancyAdjustment(guest_delta=-1, adjustment_amount=Money(amount=-2000)),
            OccupancyAdjustment(guest_delta=1, adjustment_amount=Money(amount=5000)),
        ],
    )


def _make_rate_plan_room_only() -> RatePlan:
    return RatePlan(
        id="rp-1",
        hotel_id="hotel-1",
        name="素泊まり",
        plan_type=RatePlanType.ROOM_ONLY,
        additional_charge_per_person=Money(amount=0),
    )


def _make_rate_plan_with_breakfast() -> RatePlan:
    return RatePlan(
        id="rp-2",
        hotel_id="hotel-1",
        name="朝食付き",
        plan_type=RatePlanType.WITH_BREAKFAST,
        additional_charge_per_person=Money(amount=1500),
    )


class TestCalculateDailyRates:
    def test_weekday_regular_season_room_only__base_rate_charged(self) -> None:
        # 2026-04-01 is Wednesday (weekday), Regular season
        hotel = _make_hotel()
        room_type = _make_room_type()
        rate_plan = _make_rate_plan_room_only()
        stay = StayPeriod(datetime.date(2026, 4, 1), datetime.date(2026, 4, 2))
        guest_count = GuestCount(adults=2)

        rates = calculate_daily_rates(hotel, room_type, rate_plan, stay, guest_count)

        assert len(rates) == 1
        # base 10000 * 1.0 + 0 adj + 0 plan = 10000
        assert rates[0].subtotal.amount == 10000

    def test_3_adults_in_twin_for_2__extra_bed_fee_added(self) -> None:
        # 3 adults in twin (standard=2), +5000 adjustment
        hotel = _make_hotel()
        room_type = _make_room_type()
        rate_plan = _make_rate_plan_room_only()
        stay = StayPeriod(datetime.date(2026, 4, 1), datetime.date(2026, 4, 2))
        guest_count = GuestCount(adults=3)

        rates = calculate_daily_rates(hotel, room_type, rate_plan, stay, guest_count)

        # base 10000 * 1.0 + 5000 adj + 0 plan = 15000
        assert rates[0].subtotal.amount == 15000

    def test_breakfast_plan_for_2_adults__meal_charge_per_person(self) -> None:
        hotel = _make_hotel()
        room_type = _make_room_type()
        rate_plan = _make_rate_plan_with_breakfast()
        stay = StayPeriod(datetime.date(2026, 4, 1), datetime.date(2026, 4, 2))
        guest_count = GuestCount(adults=2)

        rates = calculate_daily_rates(hotel, room_type, rate_plan, stay, guest_count)

        # base 10000 * 1.0 + 0 adj + 1500*2 plan = 13000
        assert rates[0].subtotal.amount == 13000

    def test_high_season_saturday__premium_rate_applied(self) -> None:
        hotel = _make_hotel()
        room_type = _make_room_type()
        rate_plan = _make_rate_plan_room_only()
        # 2026-07-04 is Saturday, High season
        stay = StayPeriod(datetime.date(2026, 7, 4), datetime.date(2026, 7, 5))
        guest_count = GuestCount(adults=2)

        rates = calculate_daily_rates(hotel, room_type, rate_plan, stay, guest_count)

        # base 10000 * 1.5 + 0 adj + 0 plan = 15000
        assert rates[0].subtotal.amount == 15000

    def test_school_age_child_with_breakfast__half_price_meal(self) -> None:
        hotel = _make_hotel()
        room_type = _make_room_type()
        rate_plan = _make_rate_plan_with_breakfast()
        stay = StayPeriod(datetime.date(2026, 4, 1), datetime.date(2026, 4, 2))
        # 2 adults + 1 school-age child
        guest_count = GuestCount(adults=2, child_school_age=1)

        rates = calculate_daily_rates(hotel, room_type, rate_plan, stay, guest_count)

        # base 10000 * 1.0 + 0 adj + (1500*2 + 1500*0.5*1) plan = 13750
        assert rates[0].subtotal.amount == 13750


class TestCalculateTotalAmount:
    def test_2_nights__no_length_of_stay_discount(self) -> None:
        hotel = _make_hotel()
        room_type = _make_room_type()
        rate_plan = _make_rate_plan_room_only()
        stay = StayPeriod(datetime.date(2026, 4, 1), datetime.date(2026, 4, 3))  # 2 nights
        guest_count = GuestCount(adults=2)

        rates = calculate_daily_rates(hotel, room_type, rate_plan, stay, guest_count)
        total = calculate_total_amount(rates, hotel)

        # 2 nights, no discount (< 3 nights)
        assert total.amount == 20000

    def test_3_nights__5_percent_length_of_stay_discount(self) -> None:
        hotel = _make_hotel()
        room_type = _make_room_type()
        rate_plan = _make_rate_plan_room_only()
        # 3 weekday nights in regular season
        stay = StayPeriod(datetime.date(2026, 4, 1), datetime.date(2026, 4, 4))
        guest_count = GuestCount(adults=2)

        rates = calculate_daily_rates(hotel, room_type, rate_plan, stay, guest_count)
        total = calculate_total_amount(rates, hotel)

        # Wed 10000 + Thu 10000 + Fri 11000 (1.1x) = 31000, 5% discount = 29450
        assert total.amount == 29450
