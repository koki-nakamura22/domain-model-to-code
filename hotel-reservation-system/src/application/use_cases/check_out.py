"""チェックアウトユースケース。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.events.events import GuestCheckedOut
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.repositories.room_repository import RoomRepository
from src.domain.services.event_publisher import EventPublisher


@dataclass
class CheckOutCommand:
    reservation_id: str


class CheckOutUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        room_repo: RoomRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._room_repo = room_repo
        self._event_publisher = event_publisher

    async def execute(self, command: CheckOutCommand) -> None:
        reservation = await self._reservation_repo.find_by_id(command.reservation_id)
        if not reservation:
            raise ValueError(f"Reservation not found: {command.reservation_id}")

        if not reservation.assigned_room_id:
            raise ValueError("No room assigned to this reservation")

        room = await self._room_repo.find_by_id(reservation.assigned_room_id)
        if not room:
            raise ValueError(f"Room not found: {reservation.assigned_room_id}")

        reservation.check_out()
        room.check_out()

        await self._reservation_repo.save(reservation)
        await self._room_repo.save(room)

        await self._event_publisher.publish(
            GuestCheckedOut(
                occurred_at=datetime.datetime.now(tz=datetime.UTC),
                reservation_id=reservation.id,
                reservation_number=reservation.reservation_number or "",
                hotel_id=reservation.hotel_id,
                guest_id=reservation.guest_id,
                room_id=room.id,
            )
        )
