"""RatePlan集約: 料金プランの定義。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.domain.models.shared import Money, new_id


class RatePlanType(Enum):
    ROOM_ONLY = "ROOM_ONLY"
    WITH_BREAKFAST = "WITH_BREAKFAST"
    HALF_BOARD = "HALF_BOARD"


@dataclass
class RatePlan:
    id: str
    hotel_id: str
    name: str
    plan_type: RatePlanType
    additional_charge_per_person: Money

    @staticmethod
    def create(
        hotel_id: str,
        name: str,
        plan_type: RatePlanType,
        additional_charge_per_person: Money,
    ) -> RatePlan:
        return RatePlan(
            id=new_id(),
            hotel_id=hotel_id,
            name=name,
            plan_type=plan_type,
            additional_charge_per_person=additional_charge_per_person,
        )
