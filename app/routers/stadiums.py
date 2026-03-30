"""Expose stadium discovery and management endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.schemas.stadiums import StadiumCreate
from app.services.stadiums import StadiumService


stadiumsRouter = APIRouter(
    prefix='/stadiums',
    tags=['Stadiums']
)
stadiumService = StadiumService()


@stadiumsRouter.get('/nearest')
async def get_nearest(
    lat: float,
    long: float,
    session: AsyncSession = Depends(get_session)
):
    """Return the nearest stadiums to the provided coordinates."""
    return await stadiumService.getNearestStadiums(session, lat, long)


@stadiumsRouter.get('/location')
async def get_stadiums(
    region_id: Optional[int] = None,
    district_id: Optional[int] = None,
    local_area_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """Return stadiums filtered by location hierarchy."""
    return await stadiumService.getRegionStadiums(
        session,
        region_id,
        district_id,
        local_area_id,
    )


@stadiumsRouter.get('/managed')
async def get_managed_stadiums(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Return stadiums visible to the current admin actor."""
    return await stadiumService.getManagedStadiums(session, telegram_id)


@stadiumsRouter.post('/create')
async def create_stadium(
    data: StadiumCreate,
    actor_telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Create a stadium through a superadmin-scoped endpoint."""
    new_stadium = await stadiumService.createStadium(
        session=session,
        data=data,
        actor_telegram_id=actor_telegram_id,
    )
    return {
        "message": "Muvaffaqiyatli qo'shildi.",
        "data": new_stadium.model_dump(exclude={"location"}),
        "coordinates": {"lat": data.lat, "long": data.long}
    }
