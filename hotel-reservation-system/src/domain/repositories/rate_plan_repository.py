"""RatePlanリポジトリインターフェース。"""

from __future__ import annotations

from typing import Protocol

from src.domain.models.rate_plan import RatePlan


class RatePlanRepository(Protocol):
    async def find_by_id(self, rate_plan_id: str) -> RatePlan | None: ...
    async def find_by_hotel_id(self, hotel_id: str) -> list[RatePlan]: ...
    async def save(self, rate_plan: RatePlan) -> None: ...
