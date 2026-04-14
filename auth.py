from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import Config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(identity: str, additional_claims: dict = {}) -> str:
    payload = {
        "sub": identity,
        "exp": datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS),
        **additional_claims,
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


def create_refresh_token(identity: str) -> str:
    payload = {
        "sub": identity,
        "exp": datetime.utcnow() + timedelta(days=30),
        "type": "refresh",
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_refresh_token(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency: valida un refresh token y retorna el user_id."""
    payload = _decode(token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return user_id


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency: retorna el user_id del token JWT."""
    payload = _decode(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return user_id


def require_admin(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency: valida JWT, exige perfil==3 (admin). Retorna user_id.
    No hace query a la BD — lee perfil directo del claim del token.
    """
    payload = _decode(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    if payload.get("perfil") != 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return user_id
