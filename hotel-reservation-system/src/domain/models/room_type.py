"""RoomType集約: 部屋種別の定義。定員・基準人数・基本料金・人数調整額。"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.models.shared import Money, new_id


@dataclass(frozen=True)
class Occupancy:
    standard_count: int
    max_count: int

    def __post_init__(self) -> None:
        if self.standard_count <= 0:
            raise ValueError("standard_count must be positive")
        if self.max_count < self.standard_count:
            raise ValueError("max_count must be >= standard_count")


@dataclass(frozen=True)
class OccupancyAdjustment:
    guest_delta: int
    adjustment_amount: Money


@dataclass
class RoomType:
    id: str
    hotel_id: str
    name: str
    occupancy: Occupancy
    base_rate: Money
    occupancy_adjustments: list[OccupancyAdjustment] = field(default_factory=lambda: list[OccupancyAdjustment]())

    @staticmethod
    def create(
        hotel_id: str,
        name: str,
        occupancy: Occupancy,
        base_rate: Money,
        occupancy_adjustments: list[OccupancyAdjustment] | None = None,
    ) -> RoomType:
        return RoomType(
            id=new_id(),
            hotel_id=hotel_id,
            name=name,
            occupancy=occupancy,
            base_rate=base_rate,
            occupancy_adjustments=occupancy_adjustments or [],
        )

    def calculate_occupancy_adjustment(self, adult_count: int) -> Money:
        delta = adult_count - self.occupancy.standard_count
        if delta == 0:
            return Money.zero(self.base_rate.currency)
        for adj in self.occupancy_adjustments:
            if adj.guest_delta == delta:
                return adj.adjustment_amount
        return Money.zero(self.base_rate.currency)
