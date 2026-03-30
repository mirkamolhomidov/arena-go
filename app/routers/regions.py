"""Expose location hierarchy lookup endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.schemas.regions import DistrictRead, LocalAreaRead, RegionRead
from app.services.regions import RegionService


regionsRouter = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)
regionService = RegionService()

# for regions
@regionsRouter.get("/regions", response_model=List[RegionRead])
async def get_regions(
    region_id: Optional[int] = Query(
        default=None, gt=0, description="Region id"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Return regions or a single region filter result."""
    return await regionService.list_regions(session, region_id)

# for districts
@regionsRouter.get("/districts", response_model=List[DistrictRead])
async def get_districts(
    region_id: Optional[int] = Query(
        default=None, gt=0, description="Region id"
    ),
    district_id: Optional[int] = Query(
        default=None, gt=0, description="District id"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Return districts by region or district filter."""
    return await regionService.list_districts(session, region_id, district_id)

# for local areas
@regionsRouter.get("/local-areas", response_model=List[LocalAreaRead])
async def get_local_areas(
    region_id: Optional[int] = Query(
        default=None, gt=0, description="Region id"
    ),
    district_id: Optional[int] = Query(
        default=None, gt=0, description="District id"
    ),
    local_area_id: Optional[int] = Query(
        default=None, gt=0, description="Local Area id"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Return local areas by region, district, or ID filter."""
    return await regionService.list_local_areas(
        session,
        region_id,
        district_id,
        local_area_id,
    )
