"""FastAPI ルーター定義。"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.cancel_reservation import CancelReservationCommand, CancelReservationUseCase
from src.application.use_cases.change_room_status import ChangeRoomStatusCommand, ChangeRoomStatusUseCase
from src.application.use_cases.check_in import CheckInCommand, CheckInUseCase
from src.application.use_cases.check_out import CheckOutCommand, CheckOutUseCase
from src.application.use_cases.create_reservation import CreateReservationCommand, CreateReservationUseCase
from src.application.use_cases.modify_reservation import ModifyReservationCommand, ModifyReservationUseCase
from src.application.use_cases.process_payment import ProcessPaymentCommand, ProcessPaymentUseCase
from src.domain.models.guest import ContactInfo, Guest, GuestName
from src.domain.models.hotel import CheckInOutPolicy, Hotel
from src.domain.models.payment import PaymentMethod
from src.domain.models.rate_plan import RatePlan, RatePlanType
from src.domain.models.room import Room, RoomStatus
from src.domain.models.room_type import Occupancy, RoomType
from src.domain.models.shared import Money
from src.presentation.api.dependencies import Container, get_session
from src.presentation.api.schemas import (
    CancelReservationResponse,
    ChangeRoomStatusRequest,
    CheckInRequest,
    CheckInResponse,
    CreateGuestRequest,
    CreateHotelRequest,
    CreateRatePlanRequest,
    CreateReservationRequest,
    CreateRoomRequest,
    CreateRoomTypeRequest,
    ModifyReservationRequest,
    ModifyReservationResponse,
    PaymentResponse,
    ProcessPaymentRequest,
    ReservationResponse,
)

guest_router = APIRouter(prefix="/guests", tags=["Guests"])
reservation_router = APIRouter(prefix="/reservations", tags=["Reservations"])
payment_router = APIRouter(prefix="/payments", tags=["Payments"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


def _container(session: AsyncSession) -> Container:
    return Container(session)


# === Guest ===


@guest_router.post("", status_code=201)
async def create_guest(request: CreateGuestRequest, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    c = _container(session)
    guest = Guest.create(
        name=GuestName(first_name=request.first_name, last_name=request.last_name),
        contact_info=ContactInfo(email=request.email, phone_number=request.phone_number),
    )
    await c.guest_repo.save(guest)
    return {"guest_id": guest.id}


# === Reservation ===


@reservation_router.post("", status_code=201)
async def create_reservation(
    request: CreateReservationRequest, session: AsyncSession = Depends(get_session)
) -> ReservationResponse:
    c = _container(session)
    use_case = CreateReservationUseCase(
        hotel_repo=c.hotel_repo,
        room_type_repo=c.room_type_repo,
        room_repo=c.room_repo,
        rate_plan_repo=c.rate_plan_repo,
        reservation_repo=c.reservation_repo,
        event_publisher=c.event_publisher,
    )
    try:
        result = await use_case.execute(
            CreateReservationCommand(
                hotel_id=request.hotel_id,
                guest_id=request.guest_id,
                room_type_id=request.room_type_id,
                rate_plan_id=request.rate_plan_id,
                check_in_date=request.check_in_date,
                check_out_date=request.check_out_date,
                adults=request.adults,
                child_school_age=request.child_school_age,
                child_infant=request.child_infant,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ReservationResponse(
        reservation_id=result.reservation_id,
        total_amount=result.total_amount.amount,
        currency=result.total_amount.currency.value,
        expires_at=result.expires_at,
    )


@reservation_router.put("/{reservation_id}")
async def modify_reservation(
    reservation_id: str,
    request: ModifyReservationRequest,
    session: AsyncSession = Depends(get_session),
) -> ModifyReservationResponse:
    c = _container(session)
    use_case = ModifyReservationUseCase(
        reservation_repo=c.reservation_repo,
        hotel_repo=c.hotel_repo,
        room_type_repo=c.room_type_repo,
        room_repo=c.room_repo,
        rate_plan_repo=c.rate_plan_repo,
        event_publisher=c.event_publisher,
    )
    try:
        result = await use_case.execute(
            ModifyReservationCommand(
                reservation_id=reservation_id,
                check_in_date=request.check_in_date,
                check_out_date=request.check_out_date,
                room_type_id=request.room_type_id,
                rate_plan_id=request.rate_plan_id,
                adults=request.adults,
                child_school_age=request.child_school_age,
                child_infant=request.child_infant,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ModifyReservationResponse(
        new_total_amount=result.new_total_amount.amount,
        amount_difference=result.amount_difference.amount,
        currency=result.new_total_amount.currency.value,
    )


@reservation_router.post("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: str, session: AsyncSession = Depends(get_session)
) -> CancelReservationResponse:
    c = _container(session)
    use_case = CancelReservationUseCase(
        reservation_repo=c.reservation_repo,
        hotel_repo=c.hotel_repo,
        event_publisher=c.event_publisher,
    )
    try:
        result = await use_case.execute(CancelReservationCommand(reservation_id=reservation_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return CancelReservationResponse(
        cancellation_fee=result.cancellation_fee.amount,
        refund_amount=result.refund_amount.amount,
    )


@reservation_router.post("/{reservation_id}/check-in")
async def check_in(
    reservation_id: str,
    request: CheckInRequest,
    session: AsyncSession = Depends(get_session),
) -> CheckInResponse:
    c = _container(session)
    use_case = CheckInUseCase(
        reservation_repo=c.reservation_repo,
        room_repo=c.room_repo,
        hotel_repo=c.hotel_repo,
        event_publisher=c.event_publisher,
    )
    try:
        room_number = await use_case.execute(CheckInCommand(reservation_id=reservation_id, room_id=request.room_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return CheckInResponse(room_number=room_number)


@reservation_router.post("/{reservation_id}/check-out")
async def check_out(reservation_id: str, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    c = _container(session)
    use_case = CheckOutUseCase(
        reservation_repo=c.reservation_repo,
        room_repo=c.room_repo,
        event_publisher=c.event_publisher,
    )
    try:
        await use_case.execute(CheckOutCommand(reservation_id=reservation_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "checked_out"}


# === Payment ===


@payment_router.post("", status_code=201)
async def process_payment(
    request: ProcessPaymentRequest, session: AsyncSession = Depends(get_session)
) -> PaymentResponse:
    c = _container(session)
    use_case = ProcessPaymentUseCase(
        payment_repo=c.payment_repo,
        payment_gateway=c.payment_gateway,
        event_publisher=c.event_publisher,
    )
    result = await use_case.execute(
        ProcessPaymentCommand(
            reservation_id=request.reservation_id,
            amount=Money(amount=request.amount),
            method=PaymentMethod(request.method),
            card_info=request.card_info,
        )
    )

    return PaymentResponse(
        payment_id=result.payment_id,
        success=result.success,
        failure_reason=result.failure_reason,
    )


# === Admin ===


@admin_router.post("/hotels", status_code=201)
async def create_hotel(request: CreateHotelRequest, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    c = _container(session)
    hotel = Hotel.create(
        name=request.name,
        check_in_out_policy=CheckInOutPolicy(
            check_in_time=datetime.time.fromisoformat(request.check_in_time),
            check_out_time=datetime.time.fromisoformat(request.check_out_time),
        ),
    )
    await c.hotel_repo.save(hotel)
    return {"hotel_id": hotel.id}


@admin_router.post("/room-types", status_code=201)
async def create_room_type(
    request: CreateRoomTypeRequest, session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    c = _container(session)
    room_type = RoomType.create(
        hotel_id=request.hotel_id,
        name=request.name,
        occupancy=Occupancy(standard_count=request.standard_count, max_count=request.max_count),
        base_rate=Money(amount=request.base_rate_amount),
    )
    await c.room_type_repo.save(room_type)
    return {"room_type_id": room_type.id}


@admin_router.post("/rooms", status_code=201)
async def create_room(request: CreateRoomRequest, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    c = _container(session)
    room = Room.create(
        hotel_id=request.hotel_id,
        room_type_id=request.room_type_id,
        number=request.number,
    )
    await c.room_repo.save(room)
    return {"room_id": room.id}


@admin_router.post("/rate-plans", status_code=201)
async def create_rate_plan(
    request: CreateRatePlanRequest, session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    c = _container(session)
    rate_plan = RatePlan.create(
        hotel_id=request.hotel_id,
        name=request.name,
        plan_type=RatePlanType(request.plan_type),
        additional_charge_per_person=Money(amount=request.additional_charge_per_person),
    )
    await c.rate_plan_repo.save(rate_plan)
    return {"rate_plan_id": rate_plan.id}


@admin_router.put("/rooms/{room_id}/status")
async def change_room_status(
    room_id: str,
    request: ChangeRoomStatusRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    c = _container(session)
    use_case = ChangeRoomStatusUseCase(room_repo=c.room_repo, event_publisher=c.event_publisher)
    try:
        await use_case.execute(ChangeRoomStatusCommand(room_id=room_id, new_status=RoomStatus(request.new_status)))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "updated"}


@admin_router.get("/reservations")
async def list_reservations(
    hotel_id: str,
    status: str | None = None,
    check_in_from: datetime.date | None = None,
    check_in_to: datetime.date | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int | None]]:
    c = _container(session)
    from src.domain.models.reservation import ReservationStatus as RS

    status_filter = RS(status) if status else None
    reservations = await c.reservation_repo.find_by_hotel(
        hotel_id=hotel_id, status=status_filter, check_in_from=check_in_from, check_in_to=check_in_to
    )
    return [
        {
            "reservation_id": r.id,
            "reservation_number": r.reservation_number,
            "guest_id": r.guest_id,
            "room_type_id": r.room_type_id,
            "check_in_date": r.stay_period.check_in_date.isoformat(),
            "check_out_date": r.stay_period.check_out_date.isoformat(),
            "status": r.status.value,
            "total_amount": r.total_amount.amount,
        }
        for r in reservations
    ]
