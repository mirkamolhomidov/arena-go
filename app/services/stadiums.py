from fastapi import HTTPException
from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import cast, func, text
from sqlmodel import Session, select
from typing import Optional

from app.models.districts import Districts
from app.models.local_areas import LocalAreas
from app.models.stadiums import Stadiums
from app.schemas.stadiums import StadiumCreate


class StadiumService:
    def getNearestStadiums(self, session: Session, lat: float, long: float):
        try:
            user_point = f"POINT({long} {lat})"

            distance_query = func.ST_Distance(
                Stadiums.location,
                func.ST_GeogFromText(f'SRID=4326;{user_point}')
            ).label('distance_meters')

            statement = (
                select(
                    Stadiums,
                    LocalAreas.name.label('local_area_name'),
                    distance_query,
                    func.ST_Y(cast(Stadiums.location, Geometry)).label('lat'),
                    func.ST_X(cast(Stadiums.location, Geometry)).label('long')
                )
                .join(LocalAreas, Stadiums.local_area_id == LocalAreas.id)
                .order_by(distance_query)
                .limit(3)
            )

            results = session.exec(statement).all()
            return [self._format_stadium_dict(r, has_distance=True) for r in results]
        except Exception as e:
            raise self._handle_exception(e)

    def getRegionStadiums(self, session: Session, region_id: Optional[int] = None,
                          district_id: Optional[int] = None, local_area_id: Optional[int] = None):
        try:
            statement = (
                select(
                    Stadiums,
                    LocalAreas.name.label('local_area_name'),
                    func.ST_Y(cast(Stadiums.location, Geometry)).label('lat'),
                    func.ST_X(cast(Stadiums.location, Geometry)).label('long')
                )
                .join(LocalAreas, Stadiums.local_area_id == LocalAreas.id)
            )

            if local_area_id:
                statement = statement.where(
                    Stadiums.local_area_id == local_area_id)
            elif district_id:
                statement = statement.where(
                    LocalAreas.district_id == district_id)
            elif region_id:
                statement = (
                    statement
                    .join(Districts, LocalAreas.district_id == Districts.id)
                    .where(Districts.region_id == region_id)
                )

            results = session.exec(statement).all()
            return [self._format_stadium_dict(r, has_distance=False) for r in results]

        except Exception as e:
            raise self._handle_exception(e)

    def _format_stadium_dict(self, row, has_distance: bool) -> dict:
        stadium = row[0]
        area_name = row[1]

        data = {
            "name": stadium.name,
            "address": stadium.address,
            "phone": stadium.phone,
            "working_time": stadium.working_time,
            "price_per_hour": stadium.price_per_hour,
            "status": stadium.status,
            "local_area": area_name,
            "location_url": f"https://www.google.com/maps?q={row.lat},{row.long}"
        }

        if has_distance:
            data["distance"] = self.formatDistance(row.distance_meters)

        return data

    def formatDistance(self, meters: float) -> str:
        if meters < 1000:
            return f"{int(meters)} metr"
        km = meters / 1000
        full_km = int(km)
        rem = int((km - full_km) * 1000)
        return f"{full_km} km" + (f" va {rem} metr" if rem > 0 else "")

    def createStadium(self, session: Session, data: StadiumCreate):
        try:
            stadium_data = data.model_dump(exclude={'lat', 'long'})
            db_obj = Stadiums(**stadium_data)
            point_wkt = f"POINT({data.long} {data.lat})"
            db_obj.location = WKTElement(point_wkt, srid=4326)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        except Exception as e:
            session.rollback()
            raise self._handle_exception(e)

    def _handle_exception(self, e):
        if isinstance(e, HTTPException):
            return e
        return HTTPException(status_code=500, detail=str(e))
