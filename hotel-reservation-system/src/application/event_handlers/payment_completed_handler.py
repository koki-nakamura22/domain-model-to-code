"""決済完了 → 予約確定ハンドラ。"""

from __future__ import annotations

from src.application.use_cases.confirm_reservation import ConfirmReservationCommand, ConfirmReservationUseCase
from src.domain.events.events import PaymentCompleted
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.services.event_publisher import EventPublisher


class PaymentCompletedHandler:
    def __init__(self, reservation_repo: ReservationRepository, event_publisher: EventPublisher) -> None:
        self._reservation_repo = reservation_repo
        self._event_publisher = event_publisher

    async def handle(self, event: PaymentCompleted) -> None:
        use_case = ConfirmReservationUseCase(
            reservation_repo=self._reservation_repo,
            event_publisher=self._event_publisher,
        )
        await use_case.execute(
            ConfirmReservationCommand(
                reservation_id=event.reservation_id,
                payment_id=event.payment_id,
            )
        )
