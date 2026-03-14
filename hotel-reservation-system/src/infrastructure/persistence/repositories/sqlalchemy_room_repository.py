"""Room リポジトリ SQLAlchemy 実装。"""

from __future__ import annotations

import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.room import Room, RoomStatus
from src.infrastructure.persistence.models.db_models import RoomRecord


def _to_domain(record: RoomRecord) -> Room:
    return Room(
        id=record.id,
        hotel_id=record.hotel_id,
        room_type_id=record.room_type_id,
        number=record.number,
        status=RoomStatus(record.status),
    )


def _to_record(room: Room) -> RoomRecord:
    return RoomRecord(
        id=room.id,
        hotel_id=room.hotel_id,
        room_type_id=room.room_type_id,
        number=room.number,
        status=room.status.value,
    )


class SqlAlchemyRoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, room_id: str) -> Room | None:
        result = await self._session.execute(select(RoomRecord).where(RoomRecord.id == room_id))
        record = result.scalar_one_or_none()
        return _to_domain(record) if record else None

    async def find_by_hotel_and_type(self, hotel_id: str, room_type_id: str) -> list[Room]:
        result = await self._session.execute(
            select(RoomRecord).where(and_(RoomRecord.hotel_id == hotel_id, RoomRecord.room_type_id == room_type_id))
        )
        return [_to_domain(r) for r in result.scalars().all()]

    async def find_available_by_type(self, hotel_id: str, room_type_id: str) -> list[Room]:
        result = await self._session.execute(
            select(RoomRecord).where(
                and_(
                    RoomRecord.hotel_id == hotel_id,
                    RoomRecord.room_type_id == room_type_id,
                    RoomRecord.status == RoomStatus.AVAILABLE.value,
                )
            )
        )
        return [_to_domain(r) for r in result.scalars().all()]

    async def count_available_rooms(
        self, hotel_id: str, room_type_id: str, check_in: datetime.date, check_out: datetime.date
    ) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(RoomRecord)
            .where(
                and_(
                    RoomRecord.hotel_id == hotel_id,
                    RoomRecord.room_type_id == room_type_id,
                )
            )
        )
        return result.scalar_one()

    async def save(self, room: Room) -> None:
        record = _to_record(room)
        await self._session.merge(record)
        await self._session.commit()
