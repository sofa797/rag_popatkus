import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from .config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == _hash_password(plain_password)

def _hash_password(password: str) -> str:
    salt = "kursach-salt-2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_password_hash(password: str) -> str:
    return _hash_password(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
