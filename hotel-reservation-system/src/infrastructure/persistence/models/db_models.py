"""SQLAlchemy DBモデル定義。"""

from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HotelRecord(Base):
    __tablename__ = "hotels"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    check_in_time: Mapped[str] = mapped_column(String, nullable=False)
    check_out_time: Mapped[str] = mapped_column(String, nullable=False)
    seasons_json: Mapped[str] = mapped_column(JSON, nullable=False, default="[]")
    rate_multipliers_json: Mapped[str] = mapped_column(JSON, nullable=False, default="[]")
    cancellation_policy_json: Mapped[str] = mapped_column(JSON, nullable=False, default="[]")
    length_of_stay_discount_json: Mapped[str] = mapped_column(JSON, nullable=False, default="[]")


class RoomTypeRecord(Base):
    __tablename__ = "room_types"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    hotel_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    standard_count: Mapped[int] = mapped_column(Integer, nullable=False)
    max_count: Mapped[int] = mapped_column(Integer, nullable=False)
    base_rate_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    base_rate_currency: Mapped[str] = mapped_column(String, nullable=False, default="JPY")
    occupancy_adjustments_json: Mapped[str] = mapped_column(JSON, nullable=False, default="[]")


class RoomRecord(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    hotel_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    room_type_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    number: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="AVAILABLE")


class RatePlanRecord(Base):
    __tablename__ = "rate_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    hotel_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    plan_type: Mapped[str] = mapped_column(String, nullable=False)
    additional_charge_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    additional_charge_currency: Mapped[str] = mapped_column(String, nullable=False, default="JPY")


class GuestRecord(Base):
    __tablename__ = "guests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)


class ReservationRecord(Base):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    hotel_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    guest_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    room_type_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    rate_plan_id: Mapped[str] = mapped_column(String, nullable=False)
    check_in_date: Mapped[str] = mapped_column(String, nullable=False)
    check_out_date: Mapped[str] = mapped_column(String, nullable=False)
    adults: Mapped[int] = mapped_column(Integer, nullable=False)
    child_school_age: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    child_infant: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_currency: Mapped[str] = mapped_column(String, nullable=False, default="JPY")
    reservation_number: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_room_id: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    daily_rates_json: Mapped[str] = mapped_column(JSON, nullable=False, default="[]")


class PaymentRecord(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    reservation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="JPY")
    status: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    processed_at: Mapped[str | None] = mapped_column(String, nullable=True)
