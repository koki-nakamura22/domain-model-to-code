"""Hotelリポジトリインターフェース。"""

from __future__ import annotations

from typing import Protocol

from src.domain.models.hotel import Hotel


class HotelRepository(Protocol):
    async def find_by_id(self, hotel_id: str) -> Hotel | None: ...
    async def save(self, hotel: Hotel) -> None: ...
    async def find_all(self) -> list[Hotel]: ...
