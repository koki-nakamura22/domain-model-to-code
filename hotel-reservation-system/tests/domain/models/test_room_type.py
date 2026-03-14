"""RoomType集約のテスト。"""

import pytest

from src.domain.models.room_type import Occupancy, OccupancyAdjustment, RoomType
from src.domain.models.shared import Money


class TestOccupancy:
    def test_twin_room__standard_2_max_4(self) -> None:
        occ = Occupancy(standard_count=2, max_count=4)
        assert occ.standard_count == 2

    def test_zero_capacity__rejected(self) -> None:
        with pytest.raises(ValueError):
            Occupancy(standard_count=0, max_count=2)

    def test_max_below_standard__rejected(self) -> None:
        with pytest.raises(ValueError):
            Occupancy(standard_count=3, max_count=2)


class TestRoomType:
    def test_3_adults_in_twin_for_2__extra_bed_fee_applied(self) -> None:
        rt = RoomType.create(
            hotel_id="h1",
            name="ツイン",
            occupancy=Occupancy(standard_count=2, max_count=4),
            base_rate=Money(amount=15000),
            occupancy_adjustments=[
                OccupancyAdjustment(guest_delta=-1, adjustment_amount=Money(amount=-2000)),
                OccupancyAdjustment(guest_delta=1, adjustment_amount=Money(amount=5000)),
            ],
        )
        assert rt.calculate_occupancy_adjustment(3).amount == 5000

    def test_1_adult_in_twin_for_2__single_use_discount(self) -> None:
        rt = RoomType.create(
            hotel_id="h1",
            name="ツイン",
            occupancy=Occupancy(standard_count=2, max_count=4),
            base_rate=Money(amount=15000),
            occupancy_adjustments=[
                OccupancyAdjustment(guest_delta=-1, adjustment_amount=Money(amount=-2000)),
            ],
        )
        assert rt.calculate_occupancy_adjustment(1).amount == -2000

    def test_standard_occupancy__no_adjustment(self) -> None:
        rt = RoomType.create(
            hotel_id="h1",
            name="ツイン",
            occupancy=Occupancy(standard_count=2, max_count=4),
            base_rate=Money(amount=15000),
        )
        assert rt.calculate_occupancy_adjustment(2).amount == 0
