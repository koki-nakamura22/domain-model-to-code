"""Room集約のテスト。"""

import pytest

from src.domain.models.room import Room, RoomStatus


class TestRoom:
    def test_new_room__available_for_guests(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        assert room.status == RoomStatus.AVAILABLE
        assert room.number == "101"

    def test_guest_checks_in__room_occupied(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        room.check_in()
        assert room.status == RoomStatus.OCCUPIED

    def test_guest_checks_out__room_needs_cleaning(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        room.check_in()
        room.check_out()
        assert room.status == RoomStatus.CLEANING

    def test_cleaning_done__room_available_again(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        room.check_in()
        room.check_out()
        room.mark_cleaned()
        assert room.status == RoomStatus.AVAILABLE

    def test_checkout_empty_room__rejected(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        with pytest.raises(ValueError, match="Invalid room status transition"):
            room.check_out()

    def test_set_maintenance__room_unavailable(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        room.change_status(RoomStatus.MAINTENANCE)
        assert room.status == RoomStatus.MAINTENANCE

    def test_maintenance_finished__room_available_again(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        room.change_status(RoomStatus.MAINTENANCE)
        room.change_status(RoomStatus.AVAILABLE)
        assert room.status == RoomStatus.AVAILABLE

    def test_full_turnover__checkin_checkout_cleaning_available(self) -> None:
        room = Room.create(hotel_id="h1", room_type_id="rt1", number="101")
        assert room.status == RoomStatus.AVAILABLE
        room.check_in()
        assert room.status == RoomStatus.OCCUPIED
        room.check_out()
        assert room.status == RoomStatus.CLEANING
        room.mark_cleaned()
        assert room.status == RoomStatus.AVAILABLE
