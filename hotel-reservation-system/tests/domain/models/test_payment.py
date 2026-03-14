"""Payment集約のテスト。"""

import pytest

from src.domain.models.payment import Payment, PaymentMethod, PaymentStatus
from src.domain.models.shared import Money


class TestPayment:
    def test_new_payment__pending_until_processed(self) -> None:
        payment = Payment.create(
            reservation_id="r1",
            amount=Money(amount=10000),
            method=PaymentMethod.CREDIT_CARD,
        )
        assert payment.status == PaymentStatus.PENDING
        assert payment.processed_at is None

    def test_payment_succeeds__completed_with_timestamp(self) -> None:
        payment = Payment.create("r1", Money(amount=10000), PaymentMethod.CREDIT_CARD)
        payment.complete()
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.processed_at is not None

    def test_payment_declined__marked_as_failed(self) -> None:
        payment = Payment.create("r1", Money(amount=10000), PaymentMethod.CREDIT_CARD)
        payment.fail()
        assert payment.status == PaymentStatus.FAILED

    def test_refund_after_payment__refunded(self) -> None:
        payment = Payment.create("r1", Money(amount=10000), PaymentMethod.CREDIT_CARD)
        payment.complete()
        payment.refund()
        assert payment.status == PaymentStatus.REFUNDED

    def test_double_charge__rejected(self) -> None:
        payment = Payment.create("r1", Money(amount=10000), PaymentMethod.CREDIT_CARD)
        payment.complete()
        with pytest.raises(ValueError, match="Expected payment status PENDING"):
            payment.complete()

    def test_refund_before_payment__rejected(self) -> None:
        payment = Payment.create("r1", Money(amount=10000), PaymentMethod.CREDIT_CARD)
        with pytest.raises(ValueError, match="Expected payment status COMPLETED"):
            payment.refund()
