"""Handle stadium queries, formatting, and privileged mutations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import cast, func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.error_handling import ServiceErrorHandlerMixin
from app.models.districts import Districts
from app.models.local_areas import LocalAreas
from app.models.stadium_admins import StadiumAdmins
from app.models.stadiums import Stadiums
from app.models.users import UserRole, Users
from app.schemas.stadiums import StadiumCreate


class StadiumService(ServiceErrorHandlerMixin):
    """Provide search, listing, and admin management stadium operations."""

    async def getNearestStadiums(self, session: AsyncSession, lat: float, long: float):
        """Return the closest stadiums to the given coordinates."""
        try:
            user_point = f"POINT({long} {lat})"
            distance_query = func.ST_Distance(
                Stadiums.location,
                func.ST_GeogFromText(f"SRID=4326;{user_point}")
            ).label("distance_meters")

            statement = (
                self._build_stadium_query()
                .add_columns(distance_query)
                .order_by(distance_query)
                .limit(3)
            )

            results = (await session.exec(statement)).all()
            return [self._format_stadium_dict(row, has_distance=True) for row in results]
        except Exception as error:
            raise self._handle_exception(error, action="getNearestStadiums")

    async def getRegionStadiums(
        self,
        session: AsyncSession,
        region_id: Optional[int] = None,
        district_id: Optional[int] = None,
        local_area_id: Optional[int] = None,
    ):
        """Return stadiums filtered by region, district, or local area."""
        try:
            statement = self._build_stadium_query()

            if local_area_id:
                statement = statement.where(Stadiums.local_area_id == local_area_id)
            elif district_id:
                statement = statement.where(LocalAreas.district_id == district_id)
            elif region_id:
                statement = (
                    statement
                    .join(Districts, LocalAreas.district_id == Districts.id)
                    .where(Districts.region_id == region_id)
                )

            results = (await session.exec(statement)).all()
            return [self._format_stadium_dict(row, has_distance=False) for row in results]
        except Exception as error:
            raise self._handle_exception(error, action="getRegionStadiums")

    async def getManagedStadiums(self, session: AsyncSession, telegram_id: int):
        """Return stadiums visible to the current admin or superadmin."""
        try:
            user = await self._get_user_by_telegram_id(session, telegram_id)
            statement = self._build_stadium_query()

            if user.role == UserRole.superadmin:
                statement = statement.order_by(Stadiums.name)
            elif user.role == UserRole.admin:
                statement = (
                    statement
                    .join(StadiumAdmins, StadiumAdmins.stadium_id == Stadiums.id)
                    .where(StadiumAdmins.user_id == user.id)
                    .distinct()
                    .order_by(Stadiums.name)
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Sizda admin panelga kirish huquqi yo'q",
                )

            results = (await session.exec(statement)).all()
            return [self._format_stadium_dict(row, has_distance=False) for row in results]
        except Exception as error:
            raise self._handle_exception(error, action="getManagedStadiums")

    def get_stadium_status(self, start_time, end_time) -> str:
        """Return whether the stadium is currently open or closed."""
        now = datetime.now().time()

        if start_time < end_time:
            return "open" if start_time <= now <= end_time else "closed"

        return "open" if (now >= start_time or now <= end_time) else "closed"

    def formatDistance(self, meters: float) -> str:
        """Format a meter distance into a readable Uzbek string."""
        if meters < 1000:
            return f"{int(meters)} metr"

        km = meters / 1000
        full_km = int(km)
        rem = int((km - full_km) * 1000)
        return f"{full_km} km" + (f" va {rem} metr" if rem > 0 else "")

    async def createStadium(
        self,
        session: AsyncSession,
        data: StadiumCreate,
        actor_telegram_id: int | None = None,
    ):
        """Create a new stadium record with validated point geometry."""
        try:
            if actor_telegram_id is not None:
                await self._require_superadmin(session, actor_telegram_id)

            stadium_data = data.model_dump(exclude={"lat", "long"})
            db_obj = Stadiums(**stadium_data)
            db_obj.location = WKTElement(
                f"POINT({data.long} {data.lat})",
                srid=4326,
            )
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except Exception as error:
            await session.rollback()
            raise self._handle_exception(error, action="createStadium")

    def _build_stadium_query(self):
        """Build the shared base query used by stadium listing methods."""
        return (
            select(
                Stadiums,
                LocalAreas.name.label("local_area_name"),
                func.ST_Y(cast(Stadiums.location, Geometry)).label("lat"),
                func.ST_X(cast(Stadiums.location, Geometry)).label("long"),
            )
            .join(LocalAreas, Stadiums.local_area_id == LocalAreas.id)
        )

    def _format_stadium_dict(self, row, has_distance: bool) -> dict:
        """Serialize a stadium query row into an API-friendly dictionary."""
        stadium = row[0]
        area_name = row[1]
        lat = row.lat
        long = row.long

        data = {
            "id": stadium.id,
            "name": stadium.name,
            "address": stadium.address,
            "phone": stadium.phone,
            "start_time": stadium.start_time,
            "end_time": stadium.end_time,
            "price_per_hour": stadium.price_per_hour,
            "status": self.get_stadium_status(stadium.start_time, stadium.end_time),
            "local_area": area_name,
            "lat": lat,
            "long": long,
            "location_url": f"https://www.google.com/maps?q={lat},{long}",
        }

        if has_distance:
            distance_value = getattr(row, "distance_meters", row[-1])
            distance_meters = float(distance_value or 0)
            data["distance_meters"] = distance_meters
            data["distance"] = self.formatDistance(distance_meters)

        return data

    async def _get_user_by_telegram_id(self, session: AsyncSession, telegram_id: int) -> Users:
        """Fetch a user by Telegram ID or raise a not-found error."""
        user = (
            await session.exec(
                select(Users).where(Users.telegram_id == telegram_id)
            )
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        return user

    async def _require_superadmin(self, session: AsyncSession, telegram_id: int) -> Users:
        """Ensure that the current actor has superadmin privileges."""
        user = await self._get_user_by_telegram_id(session, telegram_id)

        if user.role != UserRole.superadmin:
            raise HTTPException(
                status_code=403,
                detail="Bu amal faqat superadmin uchun ruxsat etilgan",
            )

        return user
