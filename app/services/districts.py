from typing import Optional
from app.models.districts import Districts
from sqlmodel import select


def list_districts(session, region_id: Optional[int] = None):
    statement = select(Districts)

    if region_id is not None:
        statement = statement.where(Districts.region_id == region_id)
    return session.exec(statement).all()
