"""APIリクエスト/レスポンス スキーマ。"""

from __future__ import annotations

import datetime

from pydantic import BaseModel

# === Reservation ===


class CreateReservationRequest(BaseModel):
    hotel_id: str
    guest_id: str
    room_type_id: str
    rate_plan_id: str
    check_in_date: datetime.date
    check_out_date: datetime.date
    adults: int
    child_school_age: int = 0
    child_infant: int = 0


class ReservationResponse(BaseModel):
    reservation_id: str
    total_amount: int
    currency: str = "JPY"
    expires_at: datetime.datetime | None = None
    reservation_number: str | None = None


class ModifyReservationRequest(BaseModel):
    check_in_date: datetime.date
    check_out_date: datetime.date
    room_type_id: str
    rate_plan_id: str
    adults: int
    child_school_age: int = 0
    child_infant: int = 0


class ModifyReservationResponse(BaseModel):
    new_total_amount: int
    amount_difference: int
    currency: str = "JPY"


class CancelReservationResponse(BaseModel):
    cancellation_fee: int
    refund_amount: int
    currency: str = "JPY"


# === Check-in / Check-out ===


class CheckInRequest(BaseModel):
    room_id: str


class CheckInResponse(BaseModel):
    room_number: str


# === Payment ===


class ProcessPaymentRequest(BaseModel):
    reservation_id: str
    amount: int
    method: str = "CREDIT_CARD"
    card_info: dict[str, str] = {}


class PaymentResponse(BaseModel):
    payment_id: str
    success: bool
    failure_reason: str | None = None


# === Room ===


class ChangeRoomStatusRequest(BaseModel):
    new_status: str


# === Hotel / Master ===


class CreateHotelRequest(BaseModel):
    name: str
    check_in_time: str = "15:00"
    check_out_time: str = "10:00"


class CreateRoomTypeRequest(BaseModel):
    hotel_id: str
    name: str
    standard_count: int
    max_count: int
    base_rate_amount: int


class CreateRoomRequest(BaseModel):
    hotel_id: str
    room_type_id: str
    number: str


class CreateRatePlanRequest(BaseModel):
    hotel_id: str
    name: str
    plan_type: str = "ROOM_ONLY"
    additional_charge_per_person: int = 0


class CreateGuestRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
