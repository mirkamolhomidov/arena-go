from typing import Optional

from fastapi import HTTPException
from app.models.local_areas import LocalAreas
from app.models.regions import Regions
from app.models.districts import Districts
from sqlmodel import Session, select


class RegionService:
    def list_regions(self, session: Session, region_id: int):
        try:
            statement = select(Regions)
            if region_id is not None:
                statement = statement.where(Regions.id == region_id)
            return session.exec(statement).all()
        except Exception as e:
            status_code = getattr(e, "status_code", 500)
            detail = getattr(
                e, "detail", "Serverda kutilmagan xatolik yuz berdi.")

            raise HTTPException(status_code=status_code, detail=detail)

    def list_districts(self, session: Session, region_id: int, district_id: int):
        try:
            statement = select(Districts)

            if district_id is not None:
                statement = statement.where(Districts.id == district_id)
            elif region_id is not None:
                statement = statement.where(Districts.region_id == region_id)
            return session.exec(statement).all()
        except Exception as e:
            status_code = getattr(e, "status_code", 500)
            detail = getattr(
                e, "detail", "Serverda kutilmagan xatolik yuz berdi.")

            raise HTTPException(status_code=status_code, detail=detail)

    def list_local_areas(
        self,
        session: Session,
        region_id: int,
        district_id: int,
        local_area_id: int
    ):
        try:
            statement = select(LocalAreas)
            if local_area_id:
                statement = statement.where(LocalAreas.id == local_area_id)

            elif district_id:
                statement = statement.where(
                    LocalAreas.district_id == district_id)

            elif region_id:
                statement = (
                    statement
                    .join(Districts)
                    .where(Districts.region_id == region_id)
                )
            return session.exec(statement).all()
        except Exception as e:
            status_code = getattr(e, "status_code", 500)
            detail = getattr(
                e, "detail", "Serverda kutilmagan xatolik yuz berdi.")

            raise HTTPException(status_code=status_code, detail=detail)
