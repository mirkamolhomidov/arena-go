from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.districts import DistrictRead
from app.services.districts import list_districts


router = APIRouter(prefix="/districts", tags=["districts"])


@router.get("", response_model=List[DistrictRead])
def get_districts(
    region_id: Optional[int] = Query(
        default=None, gt=0, description="Region id"
    ),
    session: Session = Depends(get_session)
):
    return list_districts(session, region_id)
