from fastapi import Request, Depends
from jose import jwt, JWTError, ExpiredSignatureError

from app.config import settings
from app.exceptions import (
    TokenExpiredException, TokenAbsentException, IncorrectTokenFormatException,
    UserIsNotPresentException,
)
from app.users.dao import UserDAO
from app.users.models import Users


def get_token(request: Request) -> str:
    """Получение токена доступа из куки"""
    token = request.cookies.get('booking_access_token')
    if not token:
        raise TokenAbsentException
    return token


async def get_current_user(token: str = Depends(get_token)) -> Users:
    """Получение пользователя из базы данных по токену доступа"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
    except ExpiredSignatureError:
        raise TokenExpiredException
    except JWTError:
        raise IncorrectTokenFormatException
    user_id: str = payload.get('sub')
    if not user_id or not user_id.isdigit():
        raise UserIsNotPresentException
    user = await UserDAO.find_one_or_none(id=int(user_id))
    if not user:
        raise UserIsNotPresentException
    return user
