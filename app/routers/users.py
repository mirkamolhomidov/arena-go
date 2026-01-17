from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.users import UserCreate
from app.services.users import UserService


usersRouter = APIRouter(
    prefix='/users',
    tags=['Users']
)
userService = UserService()

@usersRouter.post('/create')
def createUser(data: UserCreate, session: Session = Depends(get_session)):
    new_user = userService.createUser(session=session, data=data)
    
    return {
        "message": "Muvaffaqiyatli qo'shildi.",
        "data": new_user.model_dump(),
    }

@usersRouter.get('/{telegram_id}')
def get_user_by_telegram_id(
    telegram_id: int,
    session: Session = Depends(get_session)
):
    """Telegram ID orqali userni topish"""
    user = userService.getUserByTelegramId(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User topilmadi")
    return user