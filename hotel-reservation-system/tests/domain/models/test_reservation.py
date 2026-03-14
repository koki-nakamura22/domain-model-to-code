"""Reservation集約のテスト。"""

import datetime

import pytest

from src.domain.models.reservation import (
    DailyRate,
    GuestCount,
    Reservation,
    ReservationStatus,
    StayPeriod,
)
from src.domain.models.shared import Money


class TestStayPeriod:
    def test_3_night_stay__3_nights_counted(self) -> None:
        period = StayPeriod(
            check_in_date=datetime.date(2026, 4, 1),
            check_out_date=datetime.date(2026, 4, 4),
        )
        assert period.nights == 3

    def test_2_night_stay__each_stay_date_listed(self) -> None:
        period = StayPeriod(
            check_in_date=datetime.date(2026, 4, 1),
            check_out_date=datetime.date(2026, 4, 3),
        )
        assert period.stay_dates == [
            datetime.date(2026, 4, 1),
            datetime.date(2026, 4, 2),
        ]

    def test_same_day_checkin_checkout__rejected(self) -> None:
        with pytest.raises(ValueError):
            StayPeriod(
                check_in_date=datetime.date(2026, 4, 5),
                check_out_date=datetime.date(2026, 4, 5),
            )

    def test_checkout_before_checkin__rejected(self) -> None:
        with pytest.raises(ValueError):
            StayPeriod(
                check_in_date=datetime.date(2026, 4, 5),
                check_out_date=datetime.date(2026, 4, 3),
            )


class TestGuestCount:
    def test_2_adults_1_child_1_infant__4_guests_total(self) -> None:
        gc = GuestCount(adults=2, child_school_age=1, child_infant=1)
        assert gc.total == 4

    def test_2_adults_1_child_1_infant__infants_not_billed(self) -> None:
        gc = GuestCount(adults=2, child_school_age=1, child_infant=1)
        assert gc.billable_count == 3

    def test_no_adults__rejected(self) -> None:
        with pytest.raises(ValueError):
            GuestCount(adults=0)


def _make_reservation(
    status: ReservationStatus = ReservationStatus.HELD,
    expires_at: datetime.datetime | None = None,
) -> Reservation:
    daily_rate = DailyRate(
        date=datetime.date(2026, 4, 1),
        base_amount=Money(amount=10000),
        rate_multiplier=1.0,
        occupancy_adjustment=Money.zero(),
        plan_charge=Money.zero(),
    )
    return Reservation(
        id="test-res-id",
        hotel_id="test-hotel-id",
        guest_id="test-guest-id",
        room_type_id="test-room-type-id",
        rate_plan_id="test-rate-plan-id",
        stay_period=StayPeriod(
            check_in_date=datetime.date(2026, 4, 1),
            check_out_date=datetime.date(2026, 4, 2),
        ),
        guest_count=GuestCount(adults=2),
        status=status,
        daily_rates=[daily_rate],
        total_amount=Money(amount=10000),
        expires_at=expires_at or datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC),
    )


class TestReservation:
    def test_new_reservation__held_with_ttl(self) -> None:
        reservation = Reservation.hold(
            hotel_id="h1",
            guest_id="g1",
            room_type_id="rt1",
            rate_plan_id="rp1",
            stay_period=StayPeriod(datetime.date(2026, 4, 1), datetime.date(2026, 4, 3)),
            guest_count=GuestCount(adults=2),
            daily_rates=[],
            total_amount=Money(amount=20000),
            expires_at=datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC),
        )
        assert reservation.status == ReservationStatus.HELD

    def test_payment_completed__reservation_confirmed_with_number(self) -> None:
        res = _make_reservation(ReservationStatus.HELD)
        res.confirm("R-12345678")
        assert res.status == ReservationStatus.CONFIRMED
        assert res.reservation_number == "R-12345678"
        assert res.expires_at is None

    def test_confirm_already_confirmed__rejected(self) -> None:
        res = _make_reservation(ReservationStatus.CONFIRMED)
        with pytest.raises(ValueError, match="Expected status HELD"):
            res.confirm("R-12345678")

    def test_guest_cancels__reservation_cancelled(self) -> None:
        res = _make_reservation(ReservationStatus.CONFIRMED)
        res.cancel()
        assert res.status == ReservationStatus.CANCELLED

    def test_cancel_before_payment__rejected(self) -> None:
        res = _make_reservation(ReservationStatus.HELD)
        with pytest.raises(ValueError, match="Expected status CONFIRMED"):
            res.cancel()

    def test_guest_arrives__checked_in_with_room_assigned(self) -> None:
        res = _make_reservation(ReservationStatus.CONFIRMED)
        res.check_in("room-101")
        assert res.status == ReservationStatus.CHECKED_IN
        assert res.assigned_room_id == "room-101"

    def test_guest_departs__checked_out(self) -> None:
        res = _make_reservation(ReservationStatus.CHECKED_IN)
        res.check_out()
        assert res.status == ReservationStatus.CHECKED_OUT

    def test_ttl_exceeded__reservation_expired(self) -> None:
        res = _make_reservation(ReservationStatus.HELD)
        res.expire()
        assert res.status == ReservationStatus.EXPIRED

    def test_guest_never_shows_up__marked_as_no_show(self) -> None:
        res = _make_reservation(ReservationStatus.CONFIRMED)
        res.mark_no_show()
        assert res.status == ReservationStatus.NO_SHOW

    def test_full_stay__held_to_checked_out(self) -> None:
        res = _make_reservation(ReservationStatus.HELD)
        res.confirm("R-FULL")
        assert res.status == ReservationStatus.CONFIRMED
        res.check_in("room-201")
        assert res.status == ReservationStatus.CHECKED_IN
        res.check_out()
        assert res.status == ReservationStatus.CHECKED_OUT


class TestDailyRate:
    def test_high_season_saturday_with_extra_bed_and_breakfast__correct_nightly_charge(self) -> None:
        rate = DailyRate(
            date=datetime.date(2026, 4, 1),
            base_amount=Money(amount=10000),
            rate_multiplier=1.5,
            occupancy_adjustment=Money(amount=2000),
            plan_charge=Money(amount=1500),
        )
        # 10000 * 1.5 + 2000 + 1500 = 18500
        assert rate.subtotal.amount == 18500
