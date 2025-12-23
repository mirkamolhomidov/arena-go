from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.models.stadiums import Stadiums
from app.schemas.stadiums import StadiumCreate
from app.services.stadiums import StadiumService


stadiumsRouter = APIRouter(
    prefix='/stadiums',
    tags=['Stadiums']
)
stadiumService = StadiumService()


@stadiumsRouter.get('/nearest')
def get_nearest(
    lat: float,
    long: float,
    session: Session = Depends(get_session)
):
    return stadiumService.getNearestStadiums(session, lat, long)


@stadiumsRouter.get('/location')
def get_stadiums(
    region_id: Optional[int] = None,
    district_id: Optional[int] = None,
    local_area_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    return stadiumService.getRegionStadiums(session, region_id, district_id, local_area_id)


@stadiumsRouter.post('/create')
def create_stadium(
    data: StadiumCreate,
    session: Session = Depends(get_session)
):
    new_stadium = stadiumService.createStadium(session=session, data=data)
    return {
        "message": "Muvaffaqiyatli yaratildi.",
        "data": new_stadium.model_dump(exclude={"location"}),
        "coordinates": {"lat": data.lat, "long": data.long}
    }
