from typing import Optional
from app.models.local_areas import LocalAreas
from app.models.regions import Regions
from app.models.districts import Districts
from sqlmodel import Session, select


def list_regions(session: Session, region_id: int):
    statement = select(Regions)
    if region_id is not None : statement = statement.where(Regions.id == region_id)
    return session.exec(statement).all()


def list_districts(session: Session, region_id: int, district_id: int):
    statement = select(Districts)

    if district_id is not None:
        statement = statement.where(Districts.id == district_id)
    elif region_id is not None:
        statement = statement.where(Districts.region_id == region_id)
    return session.exec(statement).all()


def list_local_areas(
    session: Session,
    region_id: int,
    district_id: int,
    local_area_id: int
):
    statement = select(LocalAreas)
    if local_area_id is not None:
        statement = statement.where(LocalAreas.id == local_area_id)
    elif district_id is not None:
        statement = statement.where(LocalAreas.district_id == district_id)
    elif region_id is not None:
        statement = (
            statement
            .join(Districts, Districts.id == LocalAreas.district_id)
            .where(Districts.region_id == region_id)
            .distinct()
        )
    return session.exec(statement).all()
