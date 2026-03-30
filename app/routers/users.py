"""Expose user, admin, and superadmin management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.schemas.stadium_admins import StadiumAdminCreate
from app.schemas.users import UserCreate, UserPhoneRoleCreate
from app.services.users import UserService


usersRouter = APIRouter(
    prefix='/users',
    tags=['Users']
)
userService = UserService()


@usersRouter.post('/create')
async def createUser(data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Create or update a Telegram user profile."""
    new_user = await userService.create_user(session=session, data=data)

    return {
        "message": "Muvaffaqiyatli qo'shildi.",
        "data": new_user.model_dump(),
    }


@usersRouter.post('/create/admin')
async def createAdmin(
    data: StadiumAdminCreate,
    actor_telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Assign a user as a stadium admin."""
    new_admin = await userService.create_admin(
        session=session,
        data=data,
        actor_telegram_id=actor_telegram_id,
    )
    return {
        "message": "Muvaffaqiyatli qo'shildi.",
        "data": new_admin.model_dump(),
    }


@usersRouter.post('/create/superadmin')
async def createSuperadmin(
    data: UserPhoneRoleCreate,
    actor_telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Promote a user into the superadmin role."""
    new_superadmin = await userService.create_superadmin(
        session=session,
        data=data,
        actor_telegram_id=actor_telegram_id,
    )
    return {
        "message": "Superadmin muvaffaqiyatli qo'shildi.",
        "data": new_superadmin.model_dump(),
    }


@usersRouter.get('/superadmins')
async def get_superadmins(
    actor_telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """List all superadmins available to the acting superadmin."""
    superadmins = await userService.list_superadmins(
        session=session,
        actor_telegram_id=actor_telegram_id,
    )
    return {
        "data": superadmins,
    }


@usersRouter.delete('/superadmins/{user_id}')
async def remove_superadmin(
    user_id: int,
    actor_telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Demote a superadmin to admin or user based on remaining links."""
    removed_superadmin = await userService.remove_superadmin(
        session=session,
        user_id=user_id,
        actor_telegram_id=actor_telegram_id,
    )
    return {
        "message": "Superadmin muvaffaqiyatli olib tashlandi.",
        "data": removed_superadmin,
    }


@usersRouter.get('/stadium-admins/{stadium_id}')
async def get_stadium_admins(
    stadium_id: int,
    actor_telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """List admins assigned to a specific stadium."""
    admins = await userService.get_stadium_admins(
        session=session,
        stadium_id=stadium_id,
        actor_telegram_id=actor_telegram_id,
    )
    return {
        "data": admins
    }


@usersRouter.delete('/stadium-admins/{stadium_admin_id}')
async def remove_stadium_admin(
    stadium_admin_id: int,
    actor_telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Remove a stadium admin assignment."""
    removed_admin = await userService.remove_admin(
        session=session,
        stadium_admin_id=stadium_admin_id,
        actor_telegram_id=actor_telegram_id,
    )
    return {
        "message": "Admin muvaffaqiyatli olib tashlandi.",
        "data": removed_admin,
    }


@usersRouter.get('/{telegram_id}')
async def get_user_by_telegram_id(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Return a user profile by Telegram ID."""
    user = await userService.get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User topilmadi")
    return user
