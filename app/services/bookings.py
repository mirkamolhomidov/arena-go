from datetime import date
from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.bookings import Bookings
from app.schemas.bookings import BookingCreate


class BookingService:
    def get_booking(self, session: Session, booking_date: date):
        try:
            statement = select(Bookings)
            statement = statement.where(Bookings.booking_date == booking_date)
            return session.exec(statement).all()
        except Exception as e:
            raise self._handle_exception(e)

    def add_booking(self, session: Session, data: BookingCreate):
        try:
            data = data.model_dump()
            db_obj = Bookings(**data)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        except Exception as e:
            session.rollback()
            raise self._handle_exception(e)

    def update_booking(self, session: Session, booking_id: int, data: BookingCreate):
        try:
            db_obj = session.get(Bookings, booking_id)

            if not db_obj:
                raise HTTPException(
                    status_code=404, detail="Booking topilmadi")

            update_data = data.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_obj, key, value)

            session.commit()
            session.refresh(db_obj)

            return db_obj

        except Exception as e:
            session.rollback()
            raise self._handle_exception(e)

    def delete_booking(self, session: Session, booking_id: int):
        try:
            db_obj = session.get(Bookings, booking_id)

            if not db_obj:
                raise HTTPException(
                    status_code=404, detail="Booking topilmadi")
            session.delete(db_obj)
            session.commit()

            return {"message": "OK"}

        except Exception as e:
            session.rollback()
            raise self._handle_exception(e)

    def _handle_exception(self, e):
        if isinstance(e, HTTPException):
            return e
        return HTTPException(status_code=500, detail=str(e))
