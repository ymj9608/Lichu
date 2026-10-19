from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from app.core.config import settings
from app.core.csi_signup import verify_lab_password


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    if len(password.encode()) > 72:
        return False
    if hashed.startswith('csi-sha256$'):
        return settings.csi_lab_mode and verify_lab_password(password, hashed)
    return bcrypt.checkpw(password.encode(), hashed.encode())


def token_for(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user_id), 'iat': now, 'exp': now + timedelta(minutes=settings.access_token_minutes)}, settings.jwt_secret, algorithm='HS256')
