"""FastAPI 依存性注入。"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.event_publisher import LoggingEventPublisher
from src.infrastructure.payment.mock_payment_gateway import MockPaymentGateway
from src.infrastructure.persistence.database import async_session_factory
from src.infrastructure.persistence.repositories.sqlalchemy_hotel_repository import SqlAlchemyHotelRepository
from src.infrastructure.persistence.repositories.sqlalchemy_reservation_repository import (
    SqlAlchemyReservationRepository,
)
from src.infrastructure.persistence.repositories.sqlalchemy_room_repository import SqlAlchemyRoomRepository
from src.infrastructure.persistence.repositories.sqlalchemy_simple_repositories import (
    SqlAlchemyGuestRepository,
    SqlAlchemyPaymentRepository,
    SqlAlchemyRatePlanRepository,
    SqlAlchemyRoomTypeRepository,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


class Container:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.hotel_repo = SqlAlchemyHotelRepository(session)
        self.room_type_repo = SqlAlchemyRoomTypeRepository(session)
        self.room_repo = SqlAlchemyRoomRepository(session)
        self.rate_plan_repo = SqlAlchemyRatePlanRepository(session)
        self.guest_repo = SqlAlchemyGuestRepository(session)
        self.reservation_repo = SqlAlchemyReservationRepository(session)
        self.payment_repo = SqlAlchemyPaymentRepository(session)
        self.payment_gateway = MockPaymentGateway(always_succeed=True)
        self.event_publisher = LoggingEventPublisher()
