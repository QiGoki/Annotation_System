"""
依赖注入
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import ValidationError
from typing import Optional

from .config import settings
from ..core.database import get_db
from ..core.security import decode_token
from ..models.user import User
from ..schemas.user import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证 credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    try:
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except (KeyError, ValidationError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_current_active_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可操作"
        )
    return current_user
