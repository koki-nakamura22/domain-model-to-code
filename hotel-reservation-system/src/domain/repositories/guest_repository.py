"""Guestリポジトリインターフェース。"""

from __future__ import annotations

from typing import Protocol

from src.domain.models.guest import Guest


class GuestRepository(Protocol):
    async def find_by_id(self, guest_id: str) -> Guest | None: ...
    async def save(self, guest: Guest) -> None: ...
