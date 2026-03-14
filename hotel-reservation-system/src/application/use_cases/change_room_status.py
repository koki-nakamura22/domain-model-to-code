"""部屋ステータス変更ユースケース。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.events.events import RoomStatusChanged
from src.domain.models.room import RoomStatus
from src.domain.repositories.room_repository import RoomRepository
from src.domain.services.event_publisher import EventPublisher


@dataclass
class ChangeRoomStatusCommand:
    room_id: str
    new_status: RoomStatus


class ChangeRoomStatusUseCase:
    def __init__(
        self,
        room_repo: RoomRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._room_repo = room_repo
        self._event_publisher = event_publisher

    async def execute(self, command: ChangeRoomStatusCommand) -> None:
        room = await self._room_repo.find_by_id(command.room_id)
        if not room:
            raise ValueError(f"Room not found: {command.room_id}")

        previous_status = room.status
        room.change_status(command.new_status)

        await self._room_repo.save(room)

        await self._event_publisher.publish(
            RoomStatusChanged(
                occurred_at=datetime.datetime.now(tz=datetime.UTC),
                room_id=room.id,
                hotel_id=room.hotel_id,
                room_number=room.number,
                previous_status=previous_status,
                new_status=command.new_status,
            )
        )
