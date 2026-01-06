from datetime import date
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.bookings import BookingCreate
from app.services.bookings import BookingService


bookingsRouter = APIRouter(
    prefix='/bookings',
    tags=['Bookings']
)
bookingService = BookingService()


@bookingsRouter.get('/')
def get_booking(
    date: date,
    session: Session = Depends(get_session)
):
    bookings = bookingService.get_booking(
        session=session,
        booking_date=date
    )

    return {
        "data": bookings
    }

@bookingsRouter.post('/create-booking')
def create_booking(
    data: BookingCreate,
    session: Session = Depends(get_session)
):
    new_booking = bookingService.add_booking(
        session=session,
        data=data
    )

    return {
        "message": "Muvaffaqiyatli qo'shildi.",
        "data": new_booking
    }

@bookingsRouter.patch('/update-booking/{booking_id}')
def update_booking(
    booking_id: int,
    data: BookingCreate,
    session: Session = Depends(get_session)
):
    new_booking = bookingService.update_booking(
        session=session,
        booking_id=booking_id,
        data=data
    )

    return {
        "message": "Muvaffaqiyatli yangilandi.",
        "data": new_booking
    }
    
@bookingsRouter.delete('/delete-booking/{booking_id}')
def delete_booking(
    booking_id: int,
    session: Session = Depends(get_session)
):
    bookingService.delete_booking(
        session=session,
        booking_id=booking_id,
    )

    return {
        "message": "Muvaffaqiyatli o'chirildi.",
    }