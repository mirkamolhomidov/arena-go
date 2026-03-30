"""Handle user, admin, and superadmin management flows."""

from __future__ import annotations

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.error_handling import ServiceErrorHandlerMixin
from app.models.stadium_admins import StadiumAdmins
from app.models.users import UserRole, Users
from app.schemas.stadium_admins import StadiumAdminCreate
from app.schemas.users import UserCreate, UserPhoneRoleCreate


class UserService(ServiceErrorHandlerMixin):
    """Provide user and role management operations."""

    async def create_user(self, session: AsyncSession, data: UserCreate) -> Users:
        """Create a new user or refresh an existing Telegram user profile."""
        try:
            user = await self._get_user_by_telegram_id(session, data.telegram_id)

            if user:
                user.first_name = data.first_name
                user.username = data.username
                user.phone = data.phone
                user.local_area_id = data.local_area_id

                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user

            new_user = Users(
                first_name=data.first_name,
                username=data.username,
                telegram_id=data.telegram_id,
                phone=data.phone,
                local_area_id=data.local_area_id,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="create_user")

    async def create_admin(
        self,
        session: AsyncSession,
        data: StadiumAdminCreate,
        actor_telegram_id: int | None = None,
    ) -> StadiumAdmins:
        """Assign an existing user as an admin for a specific stadium."""
        try:
            if actor_telegram_id is not None:
                await self._require_superadmin(session, actor_telegram_id)

            user = await self._get_user_by_phone(session, data.phone)

            existing_admin = (
                await session.exec(
                    select(StadiumAdmins).where(
                        StadiumAdmins.user_id == user.id,
                        StadiumAdmins.stadium_id == data.stadium_id,
                    )
                )
            ).first()

            if existing_admin:
                raise HTTPException(
                    status_code=400,
                    detail="Bu foydalanuvchi allaqachon admin qilib tayinlangan",
                )

            if user.role != UserRole.superadmin:
                user.role = UserRole.admin
                session.add(user)

            new_admin = StadiumAdmins(user_id=user.id, stadium_id=data.stadium_id)
            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)
            return new_admin
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="create_admin")

    async def get_stadium_admins(
        self,
        session: AsyncSession,
        stadium_id: int,
        actor_telegram_id: int,
    ) -> list[dict]:
        """List all admins assigned to a single stadium."""
        try:
            await self._require_superadmin(session, actor_telegram_id)

            statement = (
                select(StadiumAdmins, Users)
                .join(Users, Users.id == StadiumAdmins.user_id)
                .where(StadiumAdmins.stadium_id == stadium_id)
                .order_by(Users.first_name)
            )

            results = (await session.exec(statement)).all()
            return [
                {
                    "stadium_admin_id": admin.id,
                    "stadium_id": admin.stadium_id,
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "first_name": user.first_name,
                    "username": user.username,
                    "phone": user.phone,
                    "role": user.role,
                }
                for admin, user in results
            ]
        except Exception as error:
            raise self._handle_exception(error, action="get_stadium_admins")

    async def remove_admin(
        self,
        session: AsyncSession,
        stadium_admin_id: int,
        actor_telegram_id: int,
    ) -> dict:
        """Remove a stadium admin assignment and normalize the user's role."""
        try:
            await self._require_superadmin(session, actor_telegram_id)

            stadium_admin = await session.get(StadiumAdmins, stadium_admin_id)
            if not stadium_admin:
                raise HTTPException(status_code=404, detail="Admin biriktiruvi topilmadi")

            user = await session.get(Users, stadium_admin.user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Admin foydalanuvchi topilmadi")

            removed_data = {
                "stadium_admin_id": stadium_admin.id,
                "stadium_id": stadium_admin.stadium_id,
                "user_id": user.id,
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "username": user.username,
                "phone": user.phone,
            }

            await session.delete(stadium_admin)
            await session.flush()

            has_remaining_admin_links = (
                await session.exec(
                    select(StadiumAdmins.id).where(StadiumAdmins.user_id == user.id)
                )
            ).first()

            if not has_remaining_admin_links and user.role == UserRole.admin:
                user.role = UserRole.user
                session.add(user)

            await session.commit()
            return removed_data
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="remove_admin")

    async def create_superadmin(
        self,
        session: AsyncSession,
        data: UserPhoneRoleCreate,
        actor_telegram_id: int,
    ) -> Users:
        """Promote an existing user into the superadmin role."""
        try:
            await self._require_superadmin(session, actor_telegram_id)
            user = await self._get_user_by_phone(session, data.phone)

            if user.role == UserRole.superadmin:
                raise HTTPException(
                    status_code=400,
                    detail="Bu foydalanuvchi allaqachon superadmin",
                )

            user.role = UserRole.superadmin
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="create_superadmin")

    async def list_superadmins(
        self,
        session: AsyncSession,
        actor_telegram_id: int,
    ) -> list[dict]:
        """Return all superadmins with removal eligibility metadata."""
        try:
            actor = await self._require_superadmin(session, actor_telegram_id)
            superadmins = (
                await session.exec(
                    select(Users)
                    .where(Users.role == UserRole.superadmin)
                    .order_by(Users.first_name)
                )
            ).all()
            total_superadmins = len(superadmins)

            return [
                {
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "first_name": user.first_name,
                    "username": user.username,
                    "phone": user.phone,
                    "can_remove": total_superadmins > 1 and user.id != actor.id,
                }
                for user in superadmins
            ]
        except Exception as error:
            raise self._handle_exception(error, action="list_superadmins")

    async def remove_superadmin(
        self,
        session: AsyncSession,
        user_id: int,
        actor_telegram_id: int,
    ) -> dict:
        """Demote a superadmin while preserving admin access when needed."""
        try:
            actor = await self._require_superadmin(session, actor_telegram_id)
            target_user = await session.get(Users, user_id)

            if not target_user:
                raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

            if target_user.role != UserRole.superadmin:
                raise HTTPException(
                    status_code=400,
                    detail="Bu foydalanuvchi superadmin emas",
                )

            if target_user.id == actor.id:
                raise HTTPException(
                    status_code=400,
                    detail="O'zingizni superadmin ro'lidan olib tashlay olmaysiz",
                )

            superadmin_count = len(
                (
                    await session.exec(
                        select(Users.id).where(Users.role == UserRole.superadmin)
                    )
                ).all()
            )
            if superadmin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Oxirgi superadminni olib tashlab bo'lmaydi",
                )

            target_user.role = await self._resolve_role_after_superadmin_removal(
                session,
                user_id=target_user.id,
            )
            session.add(target_user)
            await session.commit()
            await session.refresh(target_user)

            return {
                "user_id": target_user.id,
                "telegram_id": target_user.telegram_id,
                "first_name": target_user.first_name,
                "username": target_user.username,
                "phone": target_user.phone,
                "new_role": target_user.role,
            }
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="remove_superadmin")

    async def get_user_by_telegram_id(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> Users | None:
        """Return a user by Telegram ID when it exists."""
        try:
            return await self._get_user_by_telegram_id(session, telegram_id)
        except Exception as error:
            raise self._handle_exception(error, action="get_user_by_telegram_id")

    async def _get_user_by_telegram_id(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> Users | None:
        """Fetch a user by Telegram ID without raising an error."""
        statement = select(Users).where(Users.telegram_id == telegram_id)
        return (await session.exec(statement)).first()

    async def _get_user_by_phone(self, session: AsyncSession, phone: str) -> Users:
        """Fetch a user by phone number or raise a not-found error."""
        user = (
            await session.exec(
                select(Users).where(Users.phone == phone)
            )
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Bunday telefon raqamli user topilmadi",
            )

        return user

    async def _resolve_role_after_superadmin_removal(
        self,
        session: AsyncSession,
        *,
        user_id: int,
    ) -> UserRole:
        """Choose the fallback role after superadmin privileges are removed."""
        has_admin_links = (
            await session.exec(
                select(StadiumAdmins.id).where(StadiumAdmins.user_id == user_id)
            )
        ).first()
        return UserRole.admin if has_admin_links else UserRole.user

    async def _require_superadmin(self, session: AsyncSession, telegram_id: int) -> Users:
        """Ensure that the current actor has superadmin privileges."""
        user = await self._get_user_by_telegram_id(session, telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        if user.role != UserRole.superadmin:
            raise HTTPException(
                status_code=403,
                detail="Bu amal faqat superadmin uchun ruxsat etilgan",
            )

        return user
