"""Reservationリポジトリインターフェース。"""

from __future__ import annotations

import datetime
from typing import Protocol

from src.domain.models.reservation import Reservation, ReservationStatus


class ReservationRepository(Protocol):
    async def find_by_id(self, reservation_id: str) -> Reservation | None: ...
    async def save(self, reservation: Reservation) -> None: ...
    async def find_expired_held(self, now: datetime.datetime) -> list[Reservation]: ...
    async def find_no_shows(self, check_in_date: datetime.date) -> list[Reservation]: ...
    async def find_by_hotel(
        self,
        hotel_id: str,
        status: ReservationStatus | None = None,
        check_in_from: datetime.date | None = None,
        check_in_to: datetime.date | None = None,
    ) -> list[Reservation]: ...
    async def count_held_and_confirmed(
        self, hotel_id: str, room_type_id: str, check_in: datetime.date, check_out: datetime.date
    ) -> int: ...
