"""Handle booking creation, retrieval, and admin moderation flows."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.error_handling import ServiceErrorHandlerMixin
from app.models.bookings import BookingStatus, Bookings
from app.models.stadium_admins import StadiumAdmins
from app.models.stadiums import Stadiums
from app.models.users import UserRole, Users
from app.schemas.bookings import BookingCreate


class BookingService(ServiceErrorHandlerMixin):
    """Provide booking CRUD, validation, and scoped admin access."""

    async def get_booking(
        self,
        session: AsyncSession,
        booking_date: date | None = None,
        stadium_id: int | None = None,
        user_telegram_id: int | None = None,
        status: BookingStatus | None = BookingStatus.CONFIRMED,
    ):
        """Return bookings filtered by date, stadium, user, or status."""
        try:
            statement = select(Bookings)

            if booking_date is not None:
                statement = statement.where(Bookings.booking_date == booking_date)

            if stadium_id is not None:
                statement = statement.where(Bookings.stadium_id == stadium_id)

            if user_telegram_id is not None:
                statement = statement.where(Bookings.user_telegram_id == user_telegram_id)

            if status is not None:
                statement = statement.where(Bookings.status == status)

            statement = statement.order_by(Bookings.booking_date, Bookings.start_time)
            return (await session.exec(statement)).all()
        except Exception as error:
            raise self._handle_exception(error, action="get_booking")

    async def add_booking(self, session: AsyncSession, data: BookingCreate):
        """Create a booking after validating time, user, and stadium rules."""
        try:
            stadium = await self._get_stadium_or_404(session, data.stadium_id)
            await self._get_user_or_404(session, data.user_telegram_id)

            self._validate_stadium_hours(stadium, data)
            self._validate_booking_time(data)
            await self._ensure_time_slot_available(session, data)

            booking_data = data.model_dump()
            booking_data["status"] = data.status or BookingStatus.CONFIRMED

            db_obj = Bookings(**booking_data)
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="add_booking")

    async def update_booking(
        self,
        session: AsyncSession,
        booking_id: int,
        data: BookingCreate,
    ):
        """Update an existing booking with a validated payload."""
        try:
            db_obj = await self._get_booking_or_404(session, booking_id)
            stadium = await self._get_stadium_or_404(session, data.stadium_id)
            await self._get_user_or_404(session, data.user_telegram_id)
            self._validate_stadium_hours(stadium, data)
            self._validate_booking_time(data)
            await self._ensure_time_slot_available(
                session,
                data,
                exclude_booking_id=booking_id,
            )

            update_data = data.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_obj, key, value)

            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="update_booking")

    async def delete_booking(self, session: AsyncSession, booking_id: int):
        """Delete a booking by its primary key."""
        try:
            db_obj = await self._get_booking_or_404(session, booking_id)
            await session.delete(db_obj)
            await session.commit()
            return {"message": "OK"}
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="delete_booking")

    async def cancel_booking(
        self,
        session: AsyncSession,
        booking_id: int,
        user_telegram_id: int | None = None,
        admin_telegram_id: int | None = None,
    ):
        """Cancel a booking for its owner or a scoped admin actor."""
        try:
            db_obj = await self._get_booking_or_404(session, booking_id)

            if user_telegram_id is None and admin_telegram_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Bekor qilish uchun foydalanuvchi yoki admin identifikatori kerak",
                )

            if user_telegram_id is not None:
                if db_obj.user_telegram_id != user_telegram_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Siz faqat o'zingizning bronlaringizni bekor qila olasiz",
                    )
            else:
                admin_user, managed_stadium_ids = await self._get_admin_scope(
                    session,
                    admin_telegram_id,
                )
                if (
                    admin_user.role != UserRole.superadmin
                    and db_obj.stadium_id not in managed_stadium_ids
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Siz bu stadion bronlarini boshqara olmaysiz",
                    )

            if db_obj.status == BookingStatus.CANCELLED:
                raise HTTPException(status_code=400, detail="Bron allaqachon bekor qilingan")

            db_obj.status = BookingStatus.CANCELLED
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="cancel_booking")

    async def get_admin_bookings(
        self,
        session: AsyncSession,
        admin_telegram_id: int,
        stadium_id: int | None = None,
        booking_date: date | None = None,
        include_cancelled: bool = False,
    ):
        """Return bookings visible to an admin or superadmin."""
        try:
            admin_user, managed_stadium_ids = await self._get_admin_scope(
                session,
                admin_telegram_id,
            )

            statement = (
                select(
                    Bookings,
                    Stadiums.name.label("stadium_name"),
                    Stadiums.address.label("stadium_address"),
                    Stadiums.phone.label("stadium_phone"),
                    Users.first_name.label("customer_first_name"),
                    Users.username.label("customer_username"),
                    Users.phone.label("customer_phone"),
                )
                .join(Stadiums, Stadiums.id == Bookings.stadium_id)
                .join(Users, Users.telegram_id == Bookings.user_telegram_id)
            )

            if admin_user.role != UserRole.superadmin:
                if not managed_stadium_ids:
                    return []
                statement = statement.where(Bookings.stadium_id.in_(managed_stadium_ids))

            if stadium_id is not None:
                if (
                    admin_user.role != UserRole.superadmin
                    and stadium_id not in managed_stadium_ids
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Siz bu stadion bronlarini ko'ra olmaysiz",
                    )
                statement = statement.where(Bookings.stadium_id == stadium_id)

            if booking_date is not None:
                statement = statement.where(Bookings.booking_date == booking_date)

            if not include_cancelled:
                statement = statement.where(Bookings.status == BookingStatus.CONFIRMED)

            statement = statement.order_by(Bookings.booking_date, Bookings.start_time)
            results = (await session.exec(statement)).all()
            return [self._serialize_admin_booking(row) for row in results]
        except Exception as error:
            raise self._handle_exception(error, action="get_admin_bookings")

    async def get_user_bookings(
        self,
        session: AsyncSession,
        telegram_id: int,
        include_history: bool = False,
    ):
        """Return future or historical bookings for a single user."""
        try:
            now = datetime.now()
            statement = (
                select(
                    Bookings,
                    Stadiums.name.label("stadium_name"),
                    Stadiums.address.label("stadium_address"),
                    Stadiums.phone.label("stadium_phone"),
                    Stadiums.price_per_hour.label("price_per_hour"),
                    Stadiums.start_time.label("stadium_start_time"),
                    Stadiums.end_time.label("stadium_end_time"),
                )
                .join(Stadiums, Stadiums.id == Bookings.stadium_id)
                .where(Bookings.user_telegram_id == telegram_id)
            )

            if not include_history:
                statement = statement.where(Bookings.status == BookingStatus.CONFIRMED)
                statement = statement.where(
                    or_(
                        Bookings.booking_date > now.date(),
                        and_(
                            Bookings.booking_date == now.date(),
                            Bookings.end_time >= now.time(),
                        ),
                    )
                )

            statement = statement.order_by(Bookings.booking_date, Bookings.start_time)
            results = (await session.exec(statement)).all()
            return [self._serialize_user_booking(row) for row in results]
        except Exception as error:
            raise self._handle_exception(error, action="get_user_bookings")

    def _serialize_user_booking(self, row) -> dict:
        """Serialize a user booking row with stadium metadata."""
        booking = row[0]

        return {
            "id": booking.id,
            "stadium_id": booking.stadium_id,
            "stadium_name": row.stadium_name,
            "stadium_address": row.stadium_address,
            "stadium_phone": row.stadium_phone,
            "price_per_hour": float(row.price_per_hour or Decimal("0")),
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
            "stadium_working_hours": (
                f"{row.stadium_start_time.strftime('%H:%M')} - "
                f"{row.stadium_end_time.strftime('%H:%M')}"
            ),
        }

    def _serialize_admin_booking(self, row) -> dict:
        """Serialize an admin booking row with customer data."""
        booking = row[0]

        return {
            "id": booking.id,
            "stadium_id": booking.stadium_id,
            "stadium_name": row.stadium_name,
            "stadium_address": row.stadium_address,
            "stadium_phone": row.stadium_phone,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
            "user_telegram_id": booking.user_telegram_id,
            "customer_first_name": row.customer_first_name,
            "customer_username": row.customer_username,
            "customer_phone": row.customer_phone,
        }

    def serialize_public_booking(self, booking: Bookings) -> dict:
        """Serialize only the public booking slot fields."""
        return {
            "id": booking.id,
            "stadium_id": booking.stadium_id,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
        }

    async def _get_stadium_or_404(self, session: AsyncSession, stadium_id: int) -> Stadiums:
        """Fetch a stadium or raise a not-found error."""
        stadium = await session.get(Stadiums, stadium_id)
        if not stadium:
            raise HTTPException(status_code=404, detail="Stadion topilmadi")
        return stadium

    async def _get_user_or_404(self, session: AsyncSession, telegram_id: int) -> Users:
        """Fetch a user by Telegram ID or raise a not-found error."""
        user = (
            await session.exec(
                select(Users).where(Users.telegram_id == telegram_id)
            )
        ).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Foydalanuvchi topilmadi. Avval ro'yxatdan o'ting",
            )
        return user

    async def _get_booking_or_404(self, session: AsyncSession, booking_id: int) -> Bookings:
        """Fetch a booking by ID or raise a not-found error."""
        booking = await session.get(Bookings, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Bron topilmadi")
        return booking

    def _validate_stadium_hours(self, stadium: Stadiums, data: BookingCreate) -> None:
        """Ensure the requested booking is inside stadium working hours."""
        if data.start_time < stadium.start_time or data.end_time > stadium.end_time:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Bron vaqti stadion ish vaqtiga mos emas. "
                    f"Ish vaqti: {stadium.start_time.strftime('%H:%M')} - "
                    f"{stadium.end_time.strftime('%H:%M')}"
                ),
            )

    def _validate_booking_time(self, data: BookingCreate) -> None:
        """Reject booking requests that target time slots in the past."""
        if data.booking_date == date.today() and data.start_time <= datetime.now().time():
            raise HTTPException(
                status_code=400,
                detail="O'tib ketgan vaqtga bron qilib bo'lmaydi",
            )

    async def _ensure_time_slot_available(
        self,
        session: AsyncSession,
        data: BookingCreate,
        *,
        exclude_booking_id: int | None = None,
    ) -> None:
        """Reject overlapping confirmed bookings for the same stadium slot."""
        statement = select(Bookings).where(
            Bookings.stadium_id == data.stadium_id,
            Bookings.booking_date == data.booking_date,
            Bookings.status == BookingStatus.CONFIRMED,
            Bookings.start_time < data.end_time,
            Bookings.end_time > data.start_time,
        )

        if exclude_booking_id is not None:
            statement = statement.where(Bookings.id != exclude_booking_id)

        overlapping_booking = (await session.exec(statement)).first()

        if overlapping_booking:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Tanlangan vaqt oralig'i allaqachon band. "
                    f"Band vaqt: {overlapping_booking.start_time.strftime('%H:%M')} - "
                    f"{overlapping_booking.end_time.strftime('%H:%M')}"
                ),
            )

    async def _get_admin_scope(self, session: AsyncSession, telegram_id: int):
        """Return the actor and allowed stadium scope for admin operations."""
        user = (
            await session.exec(
                select(Users).where(Users.telegram_id == telegram_id)
            )
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        if user.role == UserRole.superadmin:
            return user, set()

        if user.role != UserRole.admin:
            raise HTTPException(
                status_code=403,
                detail="Sizda admin panelga kirish huquqi yo'q",
            )

        managed_stadium_ids = set(
            (
                await session.exec(
                    select(StadiumAdmins.stadium_id).where(
                        StadiumAdmins.user_id == user.id
                    )
                )
            ).all()
        )
        return user, managed_stadium_ids
