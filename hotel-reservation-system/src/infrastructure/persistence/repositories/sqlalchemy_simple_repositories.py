"""RoomType, RatePlan, Guest, Payment リポジトリ SQLAlchemy 実装。"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.guest import ContactInfo, Guest, GuestName
from src.domain.models.payment import Payment, PaymentMethod, PaymentStatus
from src.domain.models.rate_plan import RatePlan, RatePlanType
from src.domain.models.room_type import Occupancy, OccupancyAdjustment, RoomType
from src.domain.models.shared import Currency, Money
from src.infrastructure.persistence.models.db_models import (
    GuestRecord,
    PaymentRecord,
    RatePlanRecord,
    RoomTypeRecord,
)

# === RoomType ===


def _room_type_to_domain(record: RoomTypeRecord) -> RoomType:
    currency = Currency(record.base_rate_currency)
    adj_data: Any = record.occupancy_adjustments_json
    adjustments = [
        OccupancyAdjustment(
            guest_delta=a["guest_delta"],
            adjustment_amount=Money(amount=a["adjustment_amount"], currency=currency),
        )
        for a in adj_data
    ]
    return RoomType(
        id=record.id,
        hotel_id=record.hotel_id,
        name=record.name,
        occupancy=Occupancy(standard_count=record.standard_count, max_count=record.max_count),
        base_rate=Money(amount=record.base_rate_amount, currency=currency),
        occupancy_adjustments=adjustments,
    )


class SqlAlchemyRoomTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, room_type_id: str) -> RoomType | None:
        result = await self._session.execute(select(RoomTypeRecord).where(RoomTypeRecord.id == room_type_id))
        record = result.scalar_one_or_none()
        return _room_type_to_domain(record) if record else None

    async def find_by_hotel_id(self, hotel_id: str) -> list[RoomType]:
        result = await self._session.execute(select(RoomTypeRecord).where(RoomTypeRecord.hotel_id == hotel_id))
        return [_room_type_to_domain(r) for r in result.scalars().all()]

    async def save(self, room_type: RoomType) -> None:
        adj_json = [
            {"guest_delta": a.guest_delta, "adjustment_amount": a.adjustment_amount.amount}
            for a in room_type.occupancy_adjustments
        ]
        record = RoomTypeRecord(
            id=room_type.id,
            hotel_id=room_type.hotel_id,
            name=room_type.name,
            standard_count=room_type.occupancy.standard_count,
            max_count=room_type.occupancy.max_count,
            base_rate_amount=room_type.base_rate.amount,
            base_rate_currency=room_type.base_rate.currency.value,
            occupancy_adjustments_json=adj_json,
        )
        await self._session.merge(record)
        await self._session.flush()


# === RatePlan ===


class SqlAlchemyRatePlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, rate_plan_id: str) -> RatePlan | None:
        result = await self._session.execute(select(RatePlanRecord).where(RatePlanRecord.id == rate_plan_id))
        record = result.scalar_one_or_none()
        if not record:
            return None
        return RatePlan(
            id=record.id,
            hotel_id=record.hotel_id,
            name=record.name,
            plan_type=RatePlanType(record.plan_type),
            additional_charge_per_person=Money(
                amount=record.additional_charge_amount, currency=Currency(record.additional_charge_currency)
            ),
        )

    async def find_by_hotel_id(self, hotel_id: str) -> list[RatePlan]:
        result = await self._session.execute(select(RatePlanRecord).where(RatePlanRecord.hotel_id == hotel_id))
        return [
            RatePlan(
                id=r.id,
                hotel_id=r.hotel_id,
                name=r.name,
                plan_type=RatePlanType(r.plan_type),
                additional_charge_per_person=Money(
                    amount=r.additional_charge_amount, currency=Currency(r.additional_charge_currency)
                ),
            )
            for r in result.scalars().all()
        ]

    async def save(self, rate_plan: RatePlan) -> None:
        record = RatePlanRecord(
            id=rate_plan.id,
            hotel_id=rate_plan.hotel_id,
            name=rate_plan.name,
            plan_type=rate_plan.plan_type.value,
            additional_charge_amount=rate_plan.additional_charge_per_person.amount,
            additional_charge_currency=rate_plan.additional_charge_per_person.currency.value,
        )
        await self._session.merge(record)
        await self._session.flush()


# === Guest ===


class SqlAlchemyGuestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, guest_id: str) -> Guest | None:
        result = await self._session.execute(select(GuestRecord).where(GuestRecord.id == guest_id))
        record = result.scalar_one_or_none()
        if not record:
            return None
        return Guest(
            id=record.id,
            name=GuestName(first_name=record.first_name, last_name=record.last_name),
            contact_info=ContactInfo(email=record.email, phone_number=record.phone_number),
        )

    async def save(self, guest: Guest) -> None:
        record = GuestRecord(
            id=guest.id,
            first_name=guest.name.first_name,
            last_name=guest.name.last_name,
            email=guest.contact_info.email,
            phone_number=guest.contact_info.phone_number,
        )
        await self._session.merge(record)
        await self._session.flush()


# === Payment ===


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, payment_id: str) -> Payment | None:
        result = await self._session.execute(select(PaymentRecord).where(PaymentRecord.id == payment_id))
        record = result.scalar_one_or_none()
        if not record:
            return None
        return Payment(
            id=record.id,
            reservation_id=record.reservation_id,
            amount=Money(amount=record.amount, currency=Currency(record.currency)),
            status=PaymentStatus(record.status),
            method=PaymentMethod(record.method),
            processed_at=datetime.datetime.fromisoformat(record.processed_at) if record.processed_at else None,
        )

    async def find_by_reservation_id(self, reservation_id: str) -> list[Payment]:
        result = await self._session.execute(
            select(PaymentRecord).where(PaymentRecord.reservation_id == reservation_id)
        )
        return [
            Payment(
                id=r.id,
                reservation_id=r.reservation_id,
                amount=Money(amount=r.amount, currency=Currency(r.currency)),
                status=PaymentStatus(r.status),
                method=PaymentMethod(r.method),
                processed_at=datetime.datetime.fromisoformat(r.processed_at) if r.processed_at else None,
            )
            for r in result.scalars().all()
        ]

    async def save(self, payment: Payment) -> None:
        record = PaymentRecord(
            id=payment.id,
            reservation_id=payment.reservation_id,
            amount=payment.amount.amount,
            currency=payment.amount.currency.value,
            status=payment.status.value,
            method=payment.method.value,
            processed_at=payment.processed_at.isoformat() if payment.processed_at else None,
        )
        await self._session.merge(record)
        await self._session.flush()
