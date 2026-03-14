"""Room集約: 物理的な部屋の管理。部屋番号・ステータス。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.domain.models.shared import new_id


class RoomStatus(Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    CLEANING = "CLEANING"
    MAINTENANCE = "MAINTENANCE"


_VALID_TRANSITIONS: dict[RoomStatus, set[RoomStatus]] = {
    RoomStatus.AVAILABLE: {RoomStatus.OCCUPIED, RoomStatus.MAINTENANCE},
    RoomStatus.OCCUPIED: {RoomStatus.CLEANING},
    RoomStatus.CLEANING: {RoomStatus.AVAILABLE, RoomStatus.MAINTENANCE},
    RoomStatus.MAINTENANCE: {RoomStatus.AVAILABLE},
}


@dataclass
class Room:
    id: str
    hotel_id: str
    room_type_id: str
    number: str
    status: RoomStatus

    @staticmethod
    def create(hotel_id: str, room_type_id: str, number: str) -> Room:
        return Room(
            id=new_id(),
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            number=number,
            status=RoomStatus.AVAILABLE,
        )

    def change_status(self, new_status: RoomStatus) -> None:
        valid = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in valid:
            raise ValueError(f"Invalid room status transition: {self.status.value} -> {new_status.value}")
        self.status = new_status

    def check_in(self) -> None:
        self.change_status(RoomStatus.OCCUPIED)

    def check_out(self) -> None:
        self.change_status(RoomStatus.CLEANING)

    def mark_cleaned(self) -> None:
        self.change_status(RoomStatus.AVAILABLE)
