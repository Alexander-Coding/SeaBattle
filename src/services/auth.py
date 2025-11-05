import jwt

from datetime import datetime, timedelta
from passlib.context import CryptContext

from src import config, logger


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        config.SECRET_KEY,
        algorithm=config.ALGORITHM
    )

    logger.info(f"Access token created for: {data.get('sub')}")

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM]
        )
        return payload
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise


__all__ = [
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'decode_access_token',
]
