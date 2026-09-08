from typing import Annotated
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.entities import User

DB = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def current_user(db: DB, credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    try:
        if not credential:
            raise ValueError()
        payload = jwt.decode(credential.credentials, settings.jwt_secret, algorithms=['HS256'], options={'require': ['sub', 'exp', 'iat']})
        user = db.get(User, int(payload['sub']))
        if not user:
            raise ValueError()
        return user
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise AppError(401, 'UNAUTHORIZED', '로그인이 필요합니다.')


Actor = Annotated[User, Depends(current_user)]


def master(user: Actor):
    if user.role != 'MASTER':
        raise AppError(403, 'FORBIDDEN', '관리자 권한이 필요합니다.')
    return user


def employee(user: Actor):
    if user.role != 'USER':
        raise AppError(403, 'FORBIDDEN', '직원 전용 기능입니다.')
    return user


Master = Annotated[User, Depends(master)]
Employee = Annotated[User, Depends(employee)]
