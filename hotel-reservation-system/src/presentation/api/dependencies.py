"""FastAPI 依存性注入。"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.event_handlers.no_show_detected_notification_handler import NoShowDetectedNotificationHandler
from src.application.event_handlers.payment_completed_handler import PaymentCompletedHandler
from src.application.event_handlers.payment_failed_handler import PaymentFailedHandler
from src.application.event_handlers.payment_failed_notification_handler import PaymentFailedNotificationHandler
from src.application.event_handlers.reservation_cancelled_notification_handler import (
    ReservationCancelledNotificationHandler,
)
from src.application.event_handlers.reservation_cancelled_refund_handler import ReservationCancelledRefundHandler
from src.application.event_handlers.reservation_confirmed_notification_handler import (
    ReservationConfirmedNotificationHandler,
)
from src.application.event_handlers.reservation_modified_notification_handler import (
    ReservationModifiedNotificationHandler,
)
from src.application.event_handlers.reservation_modified_payment_handler import ReservationModifiedPaymentHandler
from src.domain.events.events import (
    NoShowDetected,
    PaymentCompleted,
    PaymentFailed,
    ReservationCancelled,
    ReservationConfirmed,
    ReservationModified,
)
from src.infrastructure.event_publisher import DispatchingEventPublisher
from src.infrastructure.notification.notification_service import LoggingNotificationService
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
    async with async_session_factory() as session, session.begin():
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
        self.notification_service = LoggingNotificationService()

        self.event_publisher = DispatchingEventPublisher()
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        ep = self.event_publisher

        # 決済完了 → 予約確定
        ep.subscribe(
            PaymentCompleted,
            PaymentCompletedHandler(
                reservation_repo=self.reservation_repo,
                event_publisher=self.event_publisher,
            ).handle,
        )

        # 決済失敗 → 仮予約失効
        ep.subscribe(
            PaymentFailed,
            PaymentFailedHandler(
                reservation_repo=self.reservation_repo,
                event_publisher=self.event_publisher,
            ).handle,
        )

        # 予約変更 → 差額決済/返金
        ep.subscribe(
            ReservationModified,
            ReservationModifiedPaymentHandler(payment_gateway=self.payment_gateway).handle,
        )

        # 予約キャンセル → 返金
        ep.subscribe(
            ReservationCancelled,
            ReservationCancelledRefundHandler(payment_gateway=self.payment_gateway).handle,
        )

        # 通知系ハンドラ
        ns = self.notification_service
        ep.subscribe(ReservationConfirmed, ReservationConfirmedNotificationHandler(notification_service=ns).handle)
        ep.subscribe(ReservationModified, ReservationModifiedNotificationHandler(notification_service=ns).handle)
        ep.subscribe(ReservationCancelled, ReservationCancelledNotificationHandler(notification_service=ns).handle)
        ep.subscribe(NoShowDetected, NoShowDetectedNotificationHandler(notification_service=ns).handle)
        ep.subscribe(PaymentFailed, PaymentFailedNotificationHandler(notification_service=ns).handle)
