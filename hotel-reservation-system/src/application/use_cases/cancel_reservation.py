"""予約キャンセルユースケース。"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.events.events import ReservationCancelled
from src.domain.models.shared import Money
from src.domain.repositories.hotel_repository import HotelRepository
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.services.event_publisher import EventPublisher


@dataclass
class CancelReservationCommand:
    reservation_id: str


@dataclass
class CancelReservationResult:
    cancellation_fee: Money
    refund_amount: Money


class CancelReservationUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        hotel_repo: HotelRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._hotel_repo = hotel_repo
        self._event_publisher = event_publisher

    async def execute(self, command: CancelReservationCommand) -> CancelReservationResult:
        reservation = await self._reservation_repo.find_by_id(command.reservation_id)
        if not reservation:
            raise ValueError(f"Reservation not found: {command.reservation_id}")

        hotel = await self._hotel_repo.find_by_id(reservation.hotel_id)
        if not hotel:
            raise ValueError(f"Hotel not found: {reservation.hotel_id}")

        cancel_date = datetime.date.today()
        cancellation_fee = hotel.calculate_cancellation_fee(
            reservation.total_amount, reservation.stay_period.check_in_date, cancel_date
        )
        refund_amount = reservation.total_amount.subtract(cancellation_fee)

        reservation.cancel()
        await self._reservation_repo.save(reservation)

        await self._event_publisher.publish(
            ReservationCancelled(
                occurred_at=datetime.datetime.now(tz=datetime.UTC),
                reservation_id=reservation.id,
                reservation_number=reservation.reservation_number or "",
                hotel_id=reservation.hotel_id,
                guest_id=reservation.guest_id,
                cancellation_fee=cancellation_fee,
                refund_amount=refund_amount,
            )
        )

        return CancelReservationResult(cancellation_fee=cancellation_fee, refund_amount=refund_amount)
