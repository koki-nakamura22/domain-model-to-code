"""仮予約作成ユースケース。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.events.events import ReservationHeld
from src.domain.models.reservation import GuestCount, Reservation, StayPeriod
from src.domain.models.shared import Money
from src.domain.repositories.hotel_repository import HotelRepository
from src.domain.repositories.rate_plan_repository import RatePlanRepository
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.repositories.room_repository import RoomRepository
from src.domain.repositories.room_type_repository import RoomTypeRepository
from src.domain.services.event_publisher import EventPublisher
from src.domain.services.pricing_service import calculate_daily_rates, calculate_total_amount

HOLD_TTL_MINUTES = 15


@dataclass
class CreateReservationCommand:
    hotel_id: str
    guest_id: str
    room_type_id: str
    rate_plan_id: str
    check_in_date: datetime.date
    check_out_date: datetime.date
    adults: int
    child_school_age: int = 0
    child_infant: int = 0


@dataclass
class CreateReservationResult:
    reservation_id: str
    total_amount: Money
    expires_at: datetime.datetime


class CreateReservationUseCase:
    def __init__(
        self,
        hotel_repo: HotelRepository,
        room_type_repo: RoomTypeRepository,
        room_repo: RoomRepository,
        rate_plan_repo: RatePlanRepository,
        reservation_repo: ReservationRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._hotel_repo = hotel_repo
        self._room_type_repo = room_type_repo
        self._room_repo = room_repo
        self._rate_plan_repo = rate_plan_repo
        self._reservation_repo = reservation_repo
        self._event_publisher = event_publisher

    async def execute(self, command: CreateReservationCommand) -> CreateReservationResult:
        hotel = await self._hotel_repo.find_by_id(command.hotel_id)
        if not hotel:
            raise ValueError(f"Hotel not found: {command.hotel_id}")

        room_type = await self._room_type_repo.find_by_id(command.room_type_id)
        if not room_type:
            raise ValueError(f"RoomType not found: {command.room_type_id}")

        rate_plan = await self._rate_plan_repo.find_by_id(command.rate_plan_id)
        if not rate_plan:
            raise ValueError(f"RatePlan not found: {command.rate_plan_id}")

        stay_period = StayPeriod(check_in_date=command.check_in_date, check_out_date=command.check_out_date)
        guest_count = GuestCount(
            adults=command.adults,
            child_school_age=command.child_school_age,
            child_infant=command.child_infant,
        )

        if guest_count.total > room_type.occupancy.max_count:
            raise ValueError(f"Guest count {guest_count.total} exceeds max occupancy {room_type.occupancy.max_count}")

        total_rooms = await self._room_repo.count_available_rooms(
            command.hotel_id, command.room_type_id, command.check_in_date, command.check_out_date
        )
        held_and_confirmed = await self._reservation_repo.count_held_and_confirmed(
            command.hotel_id, command.room_type_id, command.check_in_date, command.check_out_date
        )
        if held_and_confirmed >= total_rooms:
            raise ValueError("No rooms available for the selected period")

        daily_rates = calculate_daily_rates(hotel, room_type, rate_plan, stay_period, guest_count)
        total_amount = calculate_total_amount(daily_rates, hotel)

        expires_at = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(minutes=HOLD_TTL_MINUTES)

        reservation = Reservation.hold(
            hotel_id=command.hotel_id,
            guest_id=command.guest_id,
            room_type_id=command.room_type_id,
            rate_plan_id=command.rate_plan_id,
            stay_period=stay_period,
            guest_count=guest_count,
            daily_rates=daily_rates,
            total_amount=total_amount,
            expires_at=expires_at,
        )

        await self._reservation_repo.save(reservation)

        await self._event_publisher.publish(
            ReservationHeld(
                occurred_at=datetime.datetime.now(tz=datetime.UTC),
                reservation_id=reservation.id,
                hotel_id=command.hotel_id,
                guest_id=command.guest_id,
                room_type_id=command.room_type_id,
                rate_plan_id=command.rate_plan_id,
                stay_period=stay_period,
                guest_count=guest_count,
                total_amount=total_amount,
                expires_at=expires_at,
            )
        )

        return CreateReservationResult(
            reservation_id=reservation.id,
            total_amount=total_amount,
            expires_at=expires_at,
        )
