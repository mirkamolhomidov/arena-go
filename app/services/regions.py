"""Serve region, district, and local-area directory data."""

from __future__ import annotations

from app.core.error_handling import ServiceErrorHandlerMixin
from app.models.local_areas import LocalAreas
from app.models.regions import Regions
from app.models.districts import Districts
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


class RegionService(ServiceErrorHandlerMixin):
    """Provide lookup access to location hierarchy records."""

    async def list_regions(self, session: AsyncSession, region_id: int):
        """Return regions or a single region filtered by ID."""
        try:
            statement = select(Regions)
            if region_id is not None:
                statement = statement.where(Regions.id == region_id)
            return (await session.exec(statement)).all()
        except Exception as error:
            raise self._handle_exception(error, action="list_regions")

    async def list_districts(
        self,
        session: AsyncSession,
        region_id: int,
        district_id: int,
    ):
        """Return districts filtered by region or district ID."""
        try:
            statement = select(Districts)

            if district_id is not None:
                statement = statement.where(Districts.id == district_id)
            elif region_id is not None:
                statement = statement.where(Districts.region_id == region_id)

            return (await session.exec(statement)).all()
        except Exception as error:
            raise self._handle_exception(error, action="list_districts")

    async def list_local_areas(
        self,
        session: AsyncSession,
        region_id: int,
        district_id: int,
        local_area_id: int
    ):
        """Return local areas filtered by region, district, or local-area ID."""
        try:
            statement = select(LocalAreas)

            if local_area_id:
                statement = statement.where(LocalAreas.id == local_area_id)
            elif district_id:
                statement = statement.where(LocalAreas.district_id == district_id)
            elif region_id:
                statement = (
                    statement
                    .join(Districts)
                    .where(Districts.region_id == region_id)
                )

            return (await session.exec(statement)).all()
        except Exception as error:
            raise self._handle_exception(error, action="list_local_areas")
