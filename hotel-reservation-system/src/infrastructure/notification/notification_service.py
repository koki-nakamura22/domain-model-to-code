"""ログ出力通知サービス（スタブ実装）。"""

from __future__ import annotations

import logging

from src.domain.models.reservation import StayPeriod
from src.domain.models.shared import Money

logger = logging.getLogger(__name__)


class LoggingNotificationService:
    async def send_reservation_confirmed(
        self, guest_id: str, reservation_number: str, stay_period: StayPeriod, total_amount: Money
    ) -> None:
        logger.info(
            "Notification: reservation confirmed - guest=%s, number=%s, stay=%s~%s, amount=%s",
            guest_id,
            reservation_number,
            stay_period.check_in_date,
            stay_period.check_out_date,
            total_amount,
        )

    async def send_reservation_modified(
        self,
        guest_id: str,
        reservation_number: str,
        new_stay_period: StayPeriod,
        new_total_amount: Money,
        amount_difference: Money,
    ) -> None:
        logger.info(
            "Notification: reservation modified - guest=%s, number=%s, stay=%s~%s, new_amount=%s, diff=%s",
            guest_id,
            reservation_number,
            new_stay_period.check_in_date,
            new_stay_period.check_out_date,
            new_total_amount,
            amount_difference,
        )

    async def send_reservation_cancelled(
        self, guest_id: str, reservation_number: str, cancellation_fee: Money, refund_amount: Money
    ) -> None:
        logger.info(
            "Notification: reservation cancelled - guest=%s, number=%s, fee=%s, refund=%s",
            guest_id,
            reservation_number,
            cancellation_fee,
            refund_amount,
        )

    async def send_no_show_detected(self, guest_id: str, reservation_number: str, total_amount: Money) -> None:
        logger.info(
            "Notification: no-show detected - guest=%s, number=%s, amount=%s",
            guest_id,
            reservation_number,
            total_amount,
        )

    async def send_payment_failed(self, reservation_id: str, reason: str) -> None:
        logger.info(
            "Notification: payment failed - reservation=%s, reason=%s",
            reservation_id,
            reason,
        )
