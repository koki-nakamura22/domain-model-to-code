"""予約確定ユースケース（決済完了後に呼ばれる）。"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass

from src.domain.events.events import ReservationConfirmed
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.services.event_publisher import EventPublisher


@dataclass
class ConfirmReservationCommand:
    reservation_id: str
    payment_id: str


class ConfirmReservationUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._event_publisher = event_publisher

    async def execute(self, command: ConfirmReservationCommand) -> str:
        reservation = await self._reservation_repo.find_by_id(command.reservation_id)
        if not reservation:
            raise ValueError(f"Reservation not found: {command.reservation_id}")

        reservation_number = f"R-{uuid.uuid4().hex[:8].upper()}"
        reservation.confirm(reservation_number)

        await self._reservation_repo.save(reservation)

        await self._event_publisher.publish(
            ReservationConfirmed(
                occurred_at=datetime.datetime.now(tz=datetime.UTC),
                reservation_id=reservation.id,
                reservation_number=reservation_number,
                hotel_id=reservation.hotel_id,
                guest_id=reservation.guest_id,
                stay_period=reservation.stay_period,
                total_amount=reservation.total_amount,
                payment_id=command.payment_id,
            )
        )

        return reservation_number
