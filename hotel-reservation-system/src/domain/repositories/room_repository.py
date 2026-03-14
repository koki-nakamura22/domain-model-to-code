"""Roomリポジトリインターフェース。"""

from __future__ import annotations

import datetime
from typing import Protocol

from src.domain.models.room import Room


class RoomRepository(Protocol):
    async def find_by_id(self, room_id: str) -> Room | None: ...
    async def find_by_hotel_and_type(self, hotel_id: str, room_type_id: str) -> list[Room]: ...
    async def find_available_by_type(self, hotel_id: str, room_type_id: str) -> list[Room]: ...
    async def count_available_rooms(
        self, hotel_id: str, room_type_id: str, check_in: datetime.date, check_out: datetime.date
    ) -> int: ...
    async def save(self, room: Room) -> None: ...
