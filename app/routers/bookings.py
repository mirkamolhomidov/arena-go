"""Expose booking CRUD and scoped admin booking endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.bookings import BookingStatus
from app.schemas.bookings import BookingCreate
from app.services.bookings import BookingService


bookingsRouter = APIRouter(
    prefix='/bookings',
    tags=['Bookings']
)
bookingService = BookingService()


@bookingsRouter.get('/')
async def get_booking(
    booking_date: Optional[date] = None,
    stadium_id: Optional[int] = None,
    user_telegram_id: Optional[int] = None,
    status: Optional[BookingStatus] = BookingStatus.CONFIRMED,
    session: AsyncSession = Depends(get_session)
):
    """Return bookings using optional filters."""
    bookings = await bookingService.get_booking(
        session=session,
        booking_date=booking_date,
        stadium_id=stadium_id,
        user_telegram_id=user_telegram_id,
        status=status,
    )

    return {
        "data": [bookingService.serialize_public_booking(item) for item in bookings]
    }


@bookingsRouter.get('/my/{telegram_id}')
async def get_my_bookings(
    telegram_id: int,
    include_history: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """Return bookings for a single Telegram user."""
    bookings = await bookingService.get_user_bookings(
        session=session,
        telegram_id=telegram_id,
        include_history=include_history,
    )

    return {
        "data": bookings
    }


@bookingsRouter.get('/admin/{telegram_id}')
async def get_admin_bookings(
    telegram_id: int,
    stadium_id: Optional[int] = None,
    booking_date: Optional[date] = None,
    include_cancelled: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """Return bookings visible to an admin or superadmin."""
    bookings = await bookingService.get_admin_bookings(
        session=session,
        admin_telegram_id=telegram_id,
        stadium_id=stadium_id,
        booking_date=booking_date,
        include_cancelled=include_cancelled,
    )

    return {
        "data": bookings
    }

@bookingsRouter.post('/create-booking')
async def create_booking(
    data: BookingCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a booking after service-level validation."""
    new_booking = await bookingService.add_booking(
        session=session,
        data=data
    )

    return {
        "message": "Muvaffaqiyatli qo'shildi.",
        "data": new_booking
    }

@bookingsRouter.patch('/update-booking/{booking_id}')
async def update_booking(
    booking_id: int,
    data: BookingCreate,
    session: AsyncSession = Depends(get_session)
):
    """Update an existing booking payload."""
    new_booking = await bookingService.update_booking(
        session=session,
        booking_id=booking_id,
        data=data
    )

    return {
        "message": "Muvaffaqiyatli yangilandi.",
        "data": new_booking
    }


@bookingsRouter.patch('/cancel-booking/{booking_id}')
async def cancel_booking(
    booking_id: int,
    user_telegram_id: Optional[int] = None,
    admin_telegram_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """Cancel a booking for its owner or scoped admin."""
    cancelled_booking = await bookingService.cancel_booking(
        session=session,
        booking_id=booking_id,
        user_telegram_id=user_telegram_id,
        admin_telegram_id=admin_telegram_id,
    )

    return {
        "message": "Bron muvaffaqiyatli bekor qilindi.",
        "data": cancelled_booking
    }


@bookingsRouter.delete('/delete-booking/{booking_id}')
async def delete_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a booking by primary key."""
    await bookingService.delete_booking(
        session=session,
        booking_id=booking_id,
    )

    return {
        "message": "Muvaffaqiyatli o'chirildi.",
    }
