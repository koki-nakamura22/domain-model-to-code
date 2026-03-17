"""Reservation リポジトリ SQLAlchemy 実装。"""

from __future__ import annotations

import datetime
import json
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.reservation import (
    DailyRate,
    GuestCount,
    Reservation,
    ReservationStatus,
    StayPeriod,
)
from src.domain.models.shared import Currency, Money
from src.infrastructure.persistence.models.db_models import ReservationRecord


def _daily_rates_to_json(rates: list[DailyRate]) -> list[dict[str, Any]]:
    return [
        {
            "date": r.date.isoformat(),
            "base_amount": r.base_amount.amount,
            "rate_multiplier": r.rate_multiplier,
            "occupancy_adjustment": r.occupancy_adjustment.amount,
            "plan_charge": r.plan_charge.amount,
        }
        for r in rates
    ]


def _daily_rates_from_json(data: Any, currency: Currency) -> list[DailyRate]:
    items = json.loads(data) if isinstance(data, str) else data
    return [
        DailyRate(
            date=datetime.date.fromisoformat(r["date"]),
            base_amount=Money(amount=r["base_amount"], currency=currency),
            rate_multiplier=r["rate_multiplier"],
            occupancy_adjustment=Money(amount=r["occupancy_adjustment"], currency=currency),
            plan_charge=Money(amount=r["plan_charge"], currency=currency),
        )
        for r in items
    ]


def _to_domain(record: ReservationRecord) -> Reservation:
    currency = Currency(record.total_currency)
    return Reservation(
        id=record.id,
        hotel_id=record.hotel_id,
        guest_id=record.guest_id,
        room_type_id=record.room_type_id,
        rate_plan_id=record.rate_plan_id,
        stay_period=StayPeriod(
            check_in_date=datetime.date.fromisoformat(record.check_in_date),
            check_out_date=datetime.date.fromisoformat(record.check_out_date),
        ),
        guest_count=GuestCount(
            adults=record.adults,
            child_school_age=record.child_school_age,
            child_infant=record.child_infant,
        ),
        status=ReservationStatus(record.status),
        daily_rates=_daily_rates_from_json(record.daily_rates_json, currency),
        total_amount=Money(amount=record.total_amount, currency=currency),
        reservation_number=record.reservation_number,
        assigned_room_id=record.assigned_room_id,
        expires_at=datetime.datetime.fromisoformat(record.expires_at) if record.expires_at else None,
    )


def _to_record(reservation: Reservation) -> ReservationRecord:
    return ReservationRecord(
        id=reservation.id,
        hotel_id=reservation.hotel_id,
        guest_id=reservation.guest_id,
        room_type_id=reservation.room_type_id,
        rate_plan_id=reservation.rate_plan_id,
        check_in_date=reservation.stay_period.check_in_date.isoformat(),
        check_out_date=reservation.stay_period.check_out_date.isoformat(),
        adults=reservation.guest_count.adults,
        child_school_age=reservation.guest_count.child_school_age,
        child_infant=reservation.guest_count.child_infant,
        status=reservation.status.value,
        total_amount=reservation.total_amount.amount,
        total_currency=reservation.total_amount.currency.value,
        reservation_number=reservation.reservation_number,
        assigned_room_id=reservation.assigned_room_id,
        expires_at=reservation.expires_at.isoformat() if reservation.expires_at else None,
        daily_rates_json=_daily_rates_to_json(reservation.daily_rates),
    )


class SqlAlchemyReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, reservation_id: str) -> Reservation | None:
        result = await self._session.execute(select(ReservationRecord).where(ReservationRecord.id == reservation_id))
        record = result.scalar_one_or_none()
        return _to_domain(record) if record else None

    async def save(self, reservation: Reservation) -> None:
        record = _to_record(reservation)
        await self._session.merge(record)
        await self._session.flush()

    async def find_expired_held(self, now: datetime.datetime) -> list[Reservation]:
        result = await self._session.execute(
            select(ReservationRecord).where(
                and_(
                    ReservationRecord.status == ReservationStatus.HELD.value,
                    ReservationRecord.expires_at <= now.isoformat(),
                )
            )
        )
        return [_to_domain(r) for r in result.scalars().all()]

    async def find_no_shows(self, check_in_date: datetime.date) -> list[Reservation]:
        result = await self._session.execute(
            select(ReservationRecord).where(
                and_(
                    ReservationRecord.status == ReservationStatus.CONFIRMED.value,
                    ReservationRecord.check_in_date == check_in_date.isoformat(),
                )
            )
        )
        return [_to_domain(r) for r in result.scalars().all()]

    async def find_by_hotel(
        self,
        hotel_id: str,
        status: ReservationStatus | None = None,
        check_in_from: datetime.date | None = None,
        check_in_to: datetime.date | None = None,
    ) -> list[Reservation]:
        query = select(ReservationRecord).where(ReservationRecord.hotel_id == hotel_id)
        if status:
            query = query.where(ReservationRecord.status == status.value)
        if check_in_from:
            query = query.where(ReservationRecord.check_in_date >= check_in_from.isoformat())
        if check_in_to:
            query = query.where(ReservationRecord.check_in_date <= check_in_to.isoformat())
        result = await self._session.execute(query)
        return [_to_domain(r) for r in result.scalars().all()]

    async def count_held_and_confirmed(
        self, hotel_id: str, room_type_id: str, check_in: datetime.date, check_out: datetime.date
    ) -> int:
        result = await self._session.execute(
            select(ReservationRecord).where(
                and_(
                    ReservationRecord.hotel_id == hotel_id,
                    ReservationRecord.room_type_id == room_type_id,
                    ReservationRecord.status.in_([ReservationStatus.HELD.value, ReservationStatus.CONFIRMED.value]),
                    ReservationRecord.check_in_date < check_out.isoformat(),
                    ReservationRecord.check_out_date > check_in.isoformat(),
                )
            )
        )
        return len(result.scalars().all())
