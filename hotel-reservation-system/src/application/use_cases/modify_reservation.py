"""予約変更ユースケース。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.events.events import ReservationModified
from src.domain.models.reservation import GuestCount, StayPeriod
from src.domain.models.shared import Money
from src.domain.repositories.hotel_repository import HotelRepository
from src.domain.repositories.rate_plan_repository import RatePlanRepository
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.repositories.room_repository import RoomRepository
from src.domain.repositories.room_type_repository import RoomTypeRepository
from src.domain.services.event_publisher import EventPublisher
from src.domain.services.pricing_service import calculate_daily_rates, calculate_total_amount


@dataclass
class ModifyReservationCommand:
    reservation_id: str
    check_in_date: datetime.date
    check_out_date: datetime.date
    room_type_id: str
    rate_plan_id: str
    adults: int
    child_school_age: int = 0
    child_infant: int = 0


@dataclass
class ModifyReservationResult:
    new_total_amount: Money
    amount_difference: Money


class ModifyReservationUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        hotel_repo: HotelRepository,
        room_type_repo: RoomTypeRepository,
        room_repo: RoomRepository,
        rate_plan_repo: RatePlanRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._hotel_repo = hotel_repo
        self._room_type_repo = room_type_repo
        self._room_repo = room_repo
        self._rate_plan_repo = rate_plan_repo
        self._event_publisher = event_publisher

    async def execute(self, command: ModifyReservationCommand) -> ModifyReservationResult:
        reservation = await self._reservation_repo.find_by_id(command.reservation_id)
        if not reservation:
            raise ValueError(f"Reservation not found: {command.reservation_id}")

        hotel = await self._hotel_repo.find_by_id(reservation.hotel_id)
        if not hotel:
            raise ValueError(f"Hotel not found: {reservation.hotel_id}")

        room_type = await self._room_type_repo.find_by_id(command.room_type_id)
        if not room_type:
            raise ValueError(f"RoomType not found: {command.room_type_id}")

        rate_plan = await self._rate_plan_repo.find_by_id(command.rate_plan_id)
        if not rate_plan:
            raise ValueError(f"RatePlan not found: {command.rate_plan_id}")

        new_stay_period = StayPeriod(check_in_date=command.check_in_date, check_out_date=command.check_out_date)
        new_guest_count = GuestCount(
            adults=command.adults,
            child_school_age=command.child_school_age,
            child_infant=command.child_infant,
        )

        if new_guest_count.total > room_type.occupancy.max_count:
            raise ValueError(
                f"Guest count {new_guest_count.total} exceeds max occupancy {room_type.occupancy.max_count}"
            )

        total_rooms = await self._room_repo.count_available_rooms(
            reservation.hotel_id, command.room_type_id, command.check_in_date, command.check_out_date
        )
        held_and_confirmed = await self._reservation_repo.count_held_and_confirmed(
            reservation.hotel_id, command.room_type_id, command.check_in_date, command.check_out_date
        )
        current_reservation_counts = 1 if (reservation.room_type_id == command.room_type_id) else 0
        if held_and_confirmed - current_reservation_counts >= total_rooms:
            raise ValueError("No rooms available for the selected period")

        new_daily_rates = calculate_daily_rates(hotel, room_type, rate_plan, new_stay_period, new_guest_count)
        new_total_amount = calculate_total_amount(new_daily_rates, hotel)

        previous_stay_period = reservation.stay_period
        previous_total_amount = reservation.total_amount
        amount_difference = Money(
            amount=new_total_amount.amount - previous_total_amount.amount,
            currency=new_total_amount.currency,
        )

        reservation.modify(
            stay_period=new_stay_period,
            guest_count=new_guest_count,
            room_type_id=command.room_type_id,
            rate_plan_id=command.rate_plan_id,
            daily_rates=new_daily_rates,
            total_amount=new_total_amount,
        )

        await self._reservation_repo.save(reservation)

        await self._event_publisher.publish(
            ReservationModified(
                occurred_at=datetime.datetime.now(tz=datetime.UTC),
                reservation_id=reservation.id,
                reservation_number=reservation.reservation_number or "",
                hotel_id=reservation.hotel_id,
                guest_id=reservation.guest_id,
                previous_stay_period=previous_stay_period,
                new_stay_period=new_stay_period,
                previous_total_amount=previous_total_amount,
                new_total_amount=new_total_amount,
                amount_difference=amount_difference,
            )
        )

        return ModifyReservationResult(new_total_amount=new_total_amount, amount_difference=amount_difference)
