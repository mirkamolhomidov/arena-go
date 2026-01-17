from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.users import Users
from app.schemas.users import UserCreate


class UserService:
    def create_user(self, session: Session, data: UserCreate) -> Users:
        try:
            user = session.exec(
                select(Users).where(Users.telegram_id == data.telegram_id)
            ).first()

            if user:
                user.first_name = data.first_name
                user.username = data.username
                user.phone = data.phone
                user.local_area_id = data.local_area_id
                
                session.add(user)
                session.commit()
                session.refresh(user)
                return user

            # Create new user
            new_user = Users.model_validate(data)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user
            
        except Exception as e:
            session.rollback()
            raise self._handle_exception(e)

    def get_user_by_telegram_id(self, session: Session, telegram_id: int) -> Users | None:
        try:
            statement = select(Users).where(Users.telegram_id == telegram_id)
            return session.exec(statement).first()
        except Exception as e:
            raise self._handle_exception(e)

    def _handle_exception(self, e: Exception) -> HTTPException:
        """Handle exceptions and convert to HTTPException."""
        if isinstance(e, HTTPException):
            return e
        # Log the error here in production
        return HTTPException(status_code=500, detail=str(e))