"""Hotel集約のテスト。"""

import datetime

from src.domain.models.hotel import (
    CancellationPolicy,
    CancellationRule,
    CheckInOutPolicy,
    DayType,
    DiscountTier,
    Hotel,
    LengthOfStayDiscount,
    RateMultiplier,
    Season,
    SeasonType,
)
from src.domain.models.shared import Money


class TestSeason:
    def test_date_in_summer__belongs_to_high_season(self) -> None:
        season = Season(
            season_type=SeasonType.HIGH,
            start_date=datetime.date(2026, 7, 1),
            end_date=datetime.date(2026, 8, 31),
        )
        assert season.contains(datetime.date(2026, 7, 15))
        assert not season.contains(datetime.date(2026, 6, 30))
        assert not season.contains(datetime.date(2026, 9, 1))


class TestCancellationPolicy:
    def setup_method(self) -> None:
        self.policy = CancellationPolicy(
            rules=[
                CancellationRule(days_before_check_in=0, fee_rate=1.0),
                CancellationRule(days_before_check_in=1, fee_rate=0.5),
                CancellationRule(days_before_check_in=3, fee_rate=0.3),
                CancellationRule(days_before_check_in=7, fee_rate=0.0),
            ]
        )

    def test_cancel_on_checkin_day__full_charge(self) -> None:
        rate = self.policy.calculate_fee_rate(
            check_in_date=datetime.date(2026, 4, 10),
            cancel_date=datetime.date(2026, 4, 10),
        )
        assert rate == 1.0

    def test_cancel_1_day_before__half_charge(self) -> None:
        rate = self.policy.calculate_fee_rate(
            check_in_date=datetime.date(2026, 4, 10),
            cancel_date=datetime.date(2026, 4, 9),
        )
        assert rate == 0.5

    def test_cancel_2_days_before__30_percent_charge(self) -> None:
        rate = self.policy.calculate_fee_rate(
            check_in_date=datetime.date(2026, 4, 10),
            cancel_date=datetime.date(2026, 4, 8),
        )
        assert rate == 0.3

    def test_cancel_5_days_before__no_charge(self) -> None:
        rate = self.policy.calculate_fee_rate(
            check_in_date=datetime.date(2026, 4, 10),
            cancel_date=datetime.date(2026, 4, 5),
        )
        assert rate == 0.0

    def test_cancel_10_days_before__no_charge(self) -> None:
        rate = self.policy.calculate_fee_rate(
            check_in_date=datetime.date(2026, 4, 10),
            cancel_date=datetime.date(2026, 3, 31),
        )
        assert rate == 0.0


class TestLengthOfStayDiscount:
    def test_2_nights__no_discount(self) -> None:
        discount = LengthOfStayDiscount(
            tiers=[
                DiscountTier(min_nights=3, discount_rate=0.05),
                DiscountTier(min_nights=7, discount_rate=0.10),
            ]
        )
        assert discount.get_discount_rate(2) == 0.0

    def test_5_nights__short_stay_discount(self) -> None:
        discount = LengthOfStayDiscount(
            tiers=[
                DiscountTier(min_nights=3, discount_rate=0.05),
                DiscountTier(min_nights=7, discount_rate=0.10),
            ]
        )
        assert discount.get_discount_rate(5) == 0.05

    def test_10_nights__long_stay_discount(self) -> None:
        discount = LengthOfStayDiscount(
            tiers=[
                DiscountTier(min_nights=3, discount_rate=0.05),
                DiscountTier(min_nights=7, discount_rate=0.10),
            ]
        )
        assert discount.get_discount_rate(10) == 0.10


class TestHotel:
    def test_create__hotel_registered_with_name(self) -> None:
        hotel = Hotel.create(
            name="テストホテル",
            check_in_out_policy=CheckInOutPolicy(
                check_in_time=datetime.time(15, 0),
                check_out_time=datetime.time(10, 0),
            ),
        )
        assert hotel.name == "テストホテル"
        assert hotel.id != ""

    def test_july_date__recognized_as_high_season(self) -> None:
        hotel = Hotel.create(
            name="テストホテル",
            check_in_out_policy=CheckInOutPolicy(
                check_in_time=datetime.time(15, 0),
                check_out_time=datetime.time(10, 0),
            ),
            seasons=[
                Season(SeasonType.HIGH, datetime.date(2026, 7, 1), datetime.date(2026, 8, 31)),
                Season(SeasonType.REGULAR, datetime.date(2026, 4, 1), datetime.date(2026, 6, 30)),
            ],
        )
        season = hotel.find_season(datetime.date(2026, 7, 15))
        assert season is not None
        assert season.season_type == SeasonType.HIGH

    def test_high_season_saturday__premium_rate_applied(self) -> None:
        hotel = Hotel.create(
            name="テストホテル",
            check_in_out_policy=CheckInOutPolicy(
                check_in_time=datetime.time(15, 0),
                check_out_time=datetime.time(10, 0),
            ),
            rate_multipliers=[
                RateMultiplier(SeasonType.HIGH, DayType.SATURDAY_OR_HOLIDAY_EVE, 1.5),
                RateMultiplier(SeasonType.HIGH, DayType.WEEKDAY, 1.2),
            ],
        )
        assert hotel.get_rate_multiplier(SeasonType.HIGH, DayType.SATURDAY_OR_HOLIDAY_EVE) == 1.5
        assert hotel.get_rate_multiplier(SeasonType.HIGH, DayType.WEEKDAY) == 1.2

    def test_undefined_season_day_combo__standard_rate(self) -> None:
        hotel = Hotel.create(
            name="テストホテル",
            check_in_out_policy=CheckInOutPolicy(
                check_in_time=datetime.time(15, 0),
                check_out_time=datetime.time(10, 0),
            ),
            rate_multipliers=[
                RateMultiplier(SeasonType.HIGH, DayType.WEEKDAY, 1.2),
            ],
        )
        assert hotel.get_rate_multiplier(SeasonType.OFF, DayType.WEEKDAY) == 1.0

    def test_cancel_1_day_before__half_of_total_charged(self) -> None:
        hotel = Hotel.create(
            name="テストホテル",
            check_in_out_policy=CheckInOutPolicy(
                check_in_time=datetime.time(15, 0),
                check_out_time=datetime.time(10, 0),
            ),
            cancellation_policy=CancellationPolicy(
                rules=[
                    CancellationRule(days_before_check_in=1, fee_rate=0.5),
                    CancellationRule(days_before_check_in=7, fee_rate=0.0),
                ]
            ),
        )
        fee = hotel.calculate_cancellation_fee(
            total_amount=Money(amount=10000),
            check_in_date=datetime.date(2026, 4, 10),
            cancel_date=datetime.date(2026, 4, 9),
        )
        assert fee.amount == 5000
