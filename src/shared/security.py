from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.shared.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: Dict[str, Any] | None = None) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_minutes)
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expires}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def is_token_valid(token: str) -> bool:
    try:
        decode_token(token)
        return True
    except JWTError:
        return False