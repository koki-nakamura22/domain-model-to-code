"""Money値オブジェクトのテスト。"""

import pytest

from src.domain.models.shared import Currency, Money


class TestMoney:
    def test_default_currency__jpy(self) -> None:
        money = Money(amount=1000)
        assert money.amount == 1000
        assert money.currency == Currency.JPY

    def test_negative_amount__allowed_for_adjustments(self) -> None:
        money = Money(amount=-1000)
        assert money.amount == -1000

    def test_add__combined_amount(self) -> None:
        result = Money(amount=1000).add(Money(amount=500))
        assert result.amount == 1500

    def test_subtract__difference_amount(self) -> None:
        result = Money(amount=1000).subtract(Money(amount=300))
        assert result.amount == 700

    def test_multiply__scaled_amount(self) -> None:
        result = Money(amount=1000).multiply(1.5)
        assert result.amount == 1500

    def test_multiply_with_fraction__rounded_to_nearest_yen(self) -> None:
        result = Money(amount=1000).multiply(0.333)
        assert result.amount == 333

    def test_add_different_currencies__rejected(self) -> None:
        with pytest.raises(ValueError, match="Currency mismatch"):
            Money(amount=1000, currency=Currency.JPY).add(
                Money(amount=500, currency=Currency.USD)
            )

    def test_zero__no_charge(self) -> None:
        zero = Money.zero()
        assert zero.amount == 0
        assert zero.currency == Currency.JPY

    def test_immutable__cannot_modify_after_creation(self) -> None:
        money = Money(amount=1000)
        with pytest.raises(AttributeError):
            money.amount = 2000  # type: ignore[misc]
