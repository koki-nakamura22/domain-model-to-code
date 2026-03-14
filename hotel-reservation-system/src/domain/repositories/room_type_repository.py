"""RoomTypeリポジトリインターフェース。"""

from __future__ import annotations

from typing import Protocol

from src.domain.models.room_type import RoomType


class RoomTypeRepository(Protocol):
    async def find_by_id(self, room_type_id: str) -> RoomType | None: ...
    async def find_by_hotel_id(self, hotel_id: str) -> list[RoomType]: ...
    async def save(self, room_type: RoomType) -> None: ...
