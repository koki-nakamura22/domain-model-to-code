"""TTLバッチ: 仮予約の定期失効処理。"""

from __future__ import annotations

import asyncio
import logging

from src.application.use_cases.expire_reservations import ExpireReservationsUseCase
from src.infrastructure.event_publisher import DispatchingEventPublisher
from src.infrastructure.persistence.database import async_session_factory
from src.infrastructure.persistence.repositories.sqlalchemy_reservation_repository import (
    SqlAlchemyReservationRepository,
)

logger = logging.getLogger(__name__)

EXPIRE_INTERVAL_SECONDS = 60


async def run_expire_reservations_loop() -> None:
    while True:
        try:
            async with async_session_factory() as session, session.begin():
                reservation_repo = SqlAlchemyReservationRepository(session)
                event_publisher = DispatchingEventPublisher()
                use_case = ExpireReservationsUseCase(
                    reservation_repo=reservation_repo,
                    event_publisher=event_publisher,
                )
                expired_count = await use_case.execute()
                if expired_count > 0:
                    logger.info("Expired %d held reservations", expired_count)
        except Exception:
            logger.exception("Error in expire reservations batch")
        await asyncio.sleep(EXPIRE_INTERVAL_SECONDS)
