"""Hotel リポジトリ SQLAlchemy 実装。"""

from __future__ import annotations

import datetime
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.hotel import (
    CancellationPolicy,
    CancellationRule,
    CheckInOutPolicy,
    DayType,
    DiscountTier,
    Hotel,
    LengthOfStayDiscount,
    RateMultiplier,
    Season,
    SeasonType,
)
from src.infrastructure.persistence.models.db_models import HotelRecord


def _seasons_to_json(seasons: list[Season]) -> list[dict[str, Any]]:
    return [
        {
            "season_type": s.season_type.value,
            "start_date": s.start_date.isoformat(),
            "end_date": s.end_date.isoformat(),
        }
        for s in seasons
    ]


def _seasons_from_json(data: Any) -> list[Season]:
    items = json.loads(data) if isinstance(data, str) else data
    return [
        Season(
            season_type=SeasonType(s["season_type"]),
            start_date=datetime.date.fromisoformat(s["start_date"]),
            end_date=datetime.date.fromisoformat(s["end_date"]),
        )
        for s in items
    ]


def _rate_multipliers_to_json(multipliers: list[RateMultiplier]) -> list[dict[str, Any]]:
    return [
        {
            "season_type": rm.season_type.value,
            "day_type": rm.day_type.value,
            "multiplier": rm.multiplier,
        }
        for rm in multipliers
    ]


def _rate_multipliers_from_json(data: Any) -> list[RateMultiplier]:
    items = json.loads(data) if isinstance(data, str) else data
    return [
        RateMultiplier(
            season_type=SeasonType(rm["season_type"]),
            day_type=DayType(rm["day_type"]),
            multiplier=rm["multiplier"],
        )
        for rm in items
    ]


def _cancellation_policy_to_json(policy: CancellationPolicy) -> list[dict[str, Any]]:
    return [{"days_before_check_in": r.days_before_check_in, "fee_rate": r.fee_rate} for r in policy.rules]


def _cancellation_policy_from_json(data: Any) -> CancellationPolicy:
    items = json.loads(data) if isinstance(data, str) else data
    return CancellationPolicy(
        rules=[CancellationRule(days_before_check_in=r["days_before_check_in"], fee_rate=r["fee_rate"]) for r in items]
    )


def _discount_to_json(discount: LengthOfStayDiscount) -> list[dict[str, Any]]:
    return [{"min_nights": t.min_nights, "discount_rate": t.discount_rate} for t in discount.tiers]


def _discount_from_json(data: Any) -> LengthOfStayDiscount:
    items = json.loads(data) if isinstance(data, str) else data
    return LengthOfStayDiscount(
        tiers=[DiscountTier(min_nights=t["min_nights"], discount_rate=t["discount_rate"]) for t in items]
    )


def _to_domain(record: HotelRecord) -> Hotel:
    return Hotel(
        id=record.id,
        name=record.name,
        check_in_out_policy=CheckInOutPolicy(
            check_in_time=datetime.time.fromisoformat(record.check_in_time),
            check_out_time=datetime.time.fromisoformat(record.check_out_time),
        ),
        seasons=_seasons_from_json(record.seasons_json),
        rate_multipliers=_rate_multipliers_from_json(record.rate_multipliers_json),
        cancellation_policy=_cancellation_policy_from_json(record.cancellation_policy_json),
        length_of_stay_discount=_discount_from_json(record.length_of_stay_discount_json),
    )


def _to_record(hotel: Hotel) -> HotelRecord:
    return HotelRecord(
        id=hotel.id,
        name=hotel.name,
        check_in_time=hotel.check_in_out_policy.check_in_time.isoformat(),
        check_out_time=hotel.check_in_out_policy.check_out_time.isoformat(),
        seasons_json=_seasons_to_json(hotel.seasons),
        rate_multipliers_json=_rate_multipliers_to_json(hotel.rate_multipliers),
        cancellation_policy_json=_cancellation_policy_to_json(hotel.cancellation_policy),
        length_of_stay_discount_json=_discount_to_json(hotel.length_of_stay_discount),
    )


class SqlAlchemyHotelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, hotel_id: str) -> Hotel | None:
        result = await self._session.execute(select(HotelRecord).where(HotelRecord.id == hotel_id))
        record = result.scalar_one_or_none()
        return _to_domain(record) if record else None

    async def save(self, hotel: Hotel) -> None:
        record = _to_record(hotel)
        await self._session.merge(record)
        await self._session.flush()

    async def find_all(self) -> list[Hotel]:
        result = await self._session.execute(select(HotelRecord))
        return [_to_domain(r) for r in result.scalars().all()]
