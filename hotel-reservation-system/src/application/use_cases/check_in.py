"""チェックインユースケース。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.events.events import GuestCheckedIn
from src.domain.repositories.hotel_repository import HotelRepository
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.repositories.room_repository import RoomRepository
from src.domain.services.event_publisher import EventPublisher


@dataclass
class CheckInCommand:
    reservation_id: str
    room_id: str


class CheckInUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        room_repo: RoomRepository,
        hotel_repo: HotelRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._room_repo = room_repo
        self._hotel_repo = hotel_repo
        self._event_publisher = event_publisher

    async def execute(self, command: CheckInCommand) -> str:
        reservation = await self._reservation_repo.find_by_id(command.reservation_id)
        if not reservation:
            raise ValueError(f"Reservation not found: {command.reservation_id}")

        hotel = await self._hotel_repo.find_by_id(reservation.hotel_id)
        if not hotel:
            raise ValueError(f"Hotel not found: {reservation.hotel_id}")

        now = datetime.datetime.now(tz=datetime.UTC)
        today = now.date()
        if today < reservation.stay_period.check_in_date:
            raise ValueError("Cannot check in before the check-in date")

        current_time = now.time()
        if current_time < hotel.check_in_out_policy.check_in_time:
            raise ValueError(f"Check-in not available until {hotel.check_in_out_policy.check_in_time}")

        room = await self._room_repo.find_by_id(command.room_id)
        if not room:
            raise ValueError(f"Room not found: {command.room_id}")

        reservation.check_in(room.id)
        room.check_in()

        await self._reservation_repo.save(reservation)
        await self._room_repo.save(room)

        await self._event_publisher.publish(
            GuestCheckedIn(
                occurred_at=now,
                reservation_id=reservation.id,
                reservation_number=reservation.reservation_number or "",
                hotel_id=reservation.hotel_id,
                guest_id=reservation.guest_id,
                room_id=room.id,
                room_number=room.number,
            )
        )

        return room.number
