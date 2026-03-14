"""予約作成ユースケースのテスト。"""

import datetime

import pytest

from src.application.use_cases.create_reservation import (
    CreateReservationCommand,
    CreateReservationUseCase,
)
from src.domain.events.events import DomainEvent, ReservationHeld
from src.domain.models.hotel import (
    CheckInOutPolicy,
    DayType,
    Hotel,
    RateMultiplier,
    Season,
    SeasonType,
)
from src.domain.models.rate_plan import RatePlan, RatePlanType
from src.domain.models.reservation import Reservation, ReservationStatus
from src.domain.models.room import Room
from src.domain.models.room_type import Occupancy, RoomType
from src.domain.models.shared import Money


# === インメモリリポジトリ ===


class InMemoryHotelRepository:
    def __init__(self) -> None:
        self._data: dict[str, Hotel] = {}

    async def find_by_id(self, hotel_id: str) -> Hotel | None:
        return self._data.get(hotel_id)

    async def save(self, hotel: Hotel) -> None:
        self._data[hotel.id] = hotel

    async def find_all(self) -> list[Hotel]:
        return list(self._data.values())


class InMemoryRoomTypeRepository:
    def __init__(self) -> None:
        self._data: dict[str, RoomType] = {}

    async def find_by_id(self, room_type_id: str) -> RoomType | None:
        return self._data.get(room_type_id)

    async def find_by_hotel_id(self, hotel_id: str) -> list[RoomType]:
        return [rt for rt in self._data.values() if rt.hotel_id == hotel_id]

    async def save(self, room_type: RoomType) -> None:
        self._data[room_type.id] = room_type


class InMemoryRoomRepository:
    def __init__(self) -> None:
        self._data: dict[str, Room] = {}

    async def find_by_id(self, room_id: str) -> Room | None:
        return self._data.get(room_id)

    async def find_by_hotel_and_type(self, hotel_id: str, room_type_id: str) -> list[Room]:
        return [r for r in self._data.values() if r.hotel_id == hotel_id and r.room_type_id == room_type_id]

    async def find_available_by_type(self, hotel_id: str, room_type_id: str) -> list[Room]:
        return [
            r
            for r in self._data.values()
            if r.hotel_id == hotel_id and r.room_type_id == room_type_id and r.status.value == "AVAILABLE"
        ]

    async def count_available_rooms(
        self, hotel_id: str, room_type_id: str, check_in: datetime.date, check_out: datetime.date
    ) -> int:
        return len([r for r in self._data.values() if r.hotel_id == hotel_id and r.room_type_id == room_type_id])

    async def save(self, room: Room) -> None:
        self._data[room.id] = room


class InMemoryRatePlanRepository:
    def __init__(self) -> None:
        self._data: dict[str, RatePlan] = {}

    async def find_by_id(self, rate_plan_id: str) -> RatePlan | None:
        return self._data.get(rate_plan_id)

    async def find_by_hotel_id(self, hotel_id: str) -> list[RatePlan]:
        return [rp for rp in self._data.values() if rp.hotel_id == hotel_id]

    async def save(self, rate_plan: RatePlan) -> None:
        self._data[rate_plan.id] = rate_plan


class InMemoryReservationRepository:
    def __init__(self) -> None:
        self._data: dict[str, Reservation] = {}

    async def find_by_id(self, reservation_id: str) -> Reservation | None:
        return self._data.get(reservation_id)

    async def save(self, reservation: Reservation) -> None:
        self._data[reservation.id] = reservation

    async def find_expired_held(self, now: datetime.datetime) -> list[Reservation]:
        return [
            r
            for r in self._data.values()
            if r.status == ReservationStatus.HELD and r.expires_at is not None and r.expires_at <= now
        ]

    async def find_no_shows(self, check_in_date: datetime.date) -> list[Reservation]:
        return [
            r
            for r in self._data.values()
            if r.status == ReservationStatus.CONFIRMED and r.stay_period.check_in_date == check_in_date
        ]

    async def find_by_hotel(
        self,
        hotel_id: str,
        status: ReservationStatus | None = None,
        check_in_from: datetime.date | None = None,
        check_in_to: datetime.date | None = None,
    ) -> list[Reservation]:
        results = [r for r in self._data.values() if r.hotel_id == hotel_id]
        if status:
            results = [r for r in results if r.status == status]
        return results

    async def count_held_and_confirmed(
        self, hotel_id: str, room_type_id: str, check_in: datetime.date, check_out: datetime.date
    ) -> int:
        return len(
            [
                r
                for r in self._data.values()
                if r.hotel_id == hotel_id
                and r.room_type_id == room_type_id
                and r.status in (ReservationStatus.HELD, ReservationStatus.CONFIRMED)
                and r.stay_period.check_in_date < check_out
                and r.stay_period.check_out_date > check_in
            ]
        )


class SpyEventPublisher:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


# === テスト ===


@pytest.fixture
def hotel() -> Hotel:
    return Hotel(
        id="hotel-1",
        name="テストホテル",
        check_in_out_policy=CheckInOutPolicy(
            check_in_time=datetime.time(15, 0),
            check_out_time=datetime.time(10, 0),
        ),
        seasons=[Season(SeasonType.REGULAR, datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))],
        rate_multipliers=[RateMultiplier(SeasonType.REGULAR, DayType.WEEKDAY, 1.0)],
    )


@pytest.fixture
def room_type() -> RoomType:
    return RoomType(
        id="rt-1",
        hotel_id="hotel-1",
        name="ツイン",
        occupancy=Occupancy(standard_count=2, max_count=4),
        base_rate=Money(amount=10000),
    )


@pytest.fixture
def rate_plan() -> RatePlan:
    return RatePlan(
        id="rp-1",
        hotel_id="hotel-1",
        name="素泊まり",
        plan_type=RatePlanType.ROOM_ONLY,
        additional_charge_per_person=Money(amount=0),
    )


@pytest.fixture
def room() -> Room:
    return Room(id="room-1", hotel_id="hotel-1", room_type_id="rt-1", number="101", status=Room.create("h", "r", "1").status)


@pytest.mark.asyncio
async def test_available_room_exists__reservation_held_with_price(
    hotel: Hotel, room_type: RoomType, rate_plan: RatePlan, room: Room
) -> None:
    hotel_repo = InMemoryHotelRepository()
    await hotel_repo.save(hotel)
    room_type_repo = InMemoryRoomTypeRepository()
    await room_type_repo.save(room_type)
    rate_plan_repo = InMemoryRatePlanRepository()
    await rate_plan_repo.save(rate_plan)
    room_repo = InMemoryRoomRepository()
    await room_repo.save(room)
    reservation_repo = InMemoryReservationRepository()
    event_publisher = SpyEventPublisher()

    use_case = CreateReservationUseCase(
        hotel_repo=hotel_repo,
        room_type_repo=room_type_repo,
        room_repo=room_repo,
        rate_plan_repo=rate_plan_repo,
        reservation_repo=reservation_repo,
        event_publisher=event_publisher,
    )

    result = await use_case.execute(
        CreateReservationCommand(
            hotel_id="hotel-1",
            guest_id="guest-1",
            room_type_id="rt-1",
            rate_plan_id="rp-1",
            check_in_date=datetime.date(2026, 4, 1),
            check_out_date=datetime.date(2026, 4, 3),
            adults=2,
        )
    )

    assert result.reservation_id != ""
    assert result.total_amount.amount > 0
    assert result.expires_at is not None
    assert len(event_publisher.events) == 1
    assert isinstance(event_publisher.events[0], ReservationHeld)


@pytest.mark.asyncio
async def test_all_rooms_booked__reservation_rejected(
    hotel: Hotel, room_type: RoomType, rate_plan: RatePlan, room: Room
) -> None:
    hotel_repo = InMemoryHotelRepository()
    await hotel_repo.save(hotel)
    room_type_repo = InMemoryRoomTypeRepository()
    await room_type_repo.save(room_type)
    rate_plan_repo = InMemoryRatePlanRepository()
    await rate_plan_repo.save(rate_plan)
    room_repo = InMemoryRoomRepository()
    await room_repo.save(room)
    reservation_repo = InMemoryReservationRepository()
    event_publisher = SpyEventPublisher()

    use_case = CreateReservationUseCase(
        hotel_repo=hotel_repo,
        room_type_repo=room_type_repo,
        room_repo=room_repo,
        rate_plan_repo=rate_plan_repo,
        reservation_repo=reservation_repo,
        event_publisher=event_publisher,
    )

    # 1つ目の予約
    await use_case.execute(
        CreateReservationCommand(
            hotel_id="hotel-1",
            guest_id="guest-1",
            room_type_id="rt-1",
            rate_plan_id="rp-1",
            check_in_date=datetime.date(2026, 4, 1),
            check_out_date=datetime.date(2026, 4, 3),
            adults=2,
        )
    )

    # 2つ目の予約（同じ部屋タイプ・同じ期間、1室しかないので失敗するはず）
    with pytest.raises(ValueError, match="No rooms available"):
        await use_case.execute(
            CreateReservationCommand(
                hotel_id="hotel-1",
                guest_id="guest-2",
                room_type_id="rt-1",
                rate_plan_id="rp-1",
                check_in_date=datetime.date(2026, 4, 1),
                check_out_date=datetime.date(2026, 4, 3),
                adults=2,
            )
        )


@pytest.mark.asyncio
async def test_too_many_guests_for_room__reservation_rejected(
    hotel: Hotel, room_type: RoomType, rate_plan: RatePlan, room: Room
) -> None:
    hotel_repo = InMemoryHotelRepository()
    await hotel_repo.save(hotel)
    room_type_repo = InMemoryRoomTypeRepository()
    await room_type_repo.save(room_type)
    rate_plan_repo = InMemoryRatePlanRepository()
    await rate_plan_repo.save(rate_plan)
    room_repo = InMemoryRoomRepository()
    await room_repo.save(room)
    reservation_repo = InMemoryReservationRepository()
    event_publisher = SpyEventPublisher()

    use_case = CreateReservationUseCase(
        hotel_repo=hotel_repo,
        room_type_repo=room_type_repo,
        room_repo=room_repo,
        rate_plan_repo=rate_plan_repo,
        reservation_repo=reservation_repo,
        event_publisher=event_publisher,
    )

    with pytest.raises(ValueError, match="exceeds max occupancy"):
        await use_case.execute(
            CreateReservationCommand(
                hotel_id="hotel-1",
                guest_id="guest-1",
                room_type_id="rt-1",
                rate_plan_id="rp-1",
                check_in_date=datetime.date(2026, 4, 1),
                check_out_date=datetime.date(2026, 4, 3),
                adults=5,
            )
        )
