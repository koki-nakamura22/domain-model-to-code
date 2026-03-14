"""ノーショー検出ユースケース。"""

from __future__ import annotations

import datetime

from src.domain.events.events import NoShowDetected
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.services.event_publisher import EventPublisher


class DetectNoShowsUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._event_publisher = event_publisher

    async def execute(self) -> int:
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        no_shows = await self._reservation_repo.find_no_shows(yesterday)

        now = datetime.datetime.now(tz=datetime.UTC)
        for reservation in no_shows:
            reservation.mark_no_show()
            await self._reservation_repo.save(reservation)
            await self._event_publisher.publish(
                NoShowDetected(
                    occurred_at=now,
                    reservation_id=reservation.id,
                    reservation_number=reservation.reservation_number or "",
                    hotel_id=reservation.hotel_id,
                    guest_id=reservation.guest_id,
                    total_amount=reservation.total_amount,
                )
            )

        return len(no_shows)
