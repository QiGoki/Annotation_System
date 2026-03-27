"""
用户服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash


class UserService:
    """用户服务类"""

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == user_in.username).first()
        if existing_user:
            raise ValueError(f"用户名 {user_in.username} 已存在")

        user = User(
            username=user_in.username,
            password_hash=get_password_hash(user_in.password),
            role=user_in.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[User]:
        """获取用户列表"""
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        if keyword:
            query = query.filter(User.username.contains(keyword))
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_users_total(db: Session, role: Optional[str] = None, keyword: Optional[str] = None) -> int:
        """获取用户总数"""
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        if keyword:
            query = query.filter(User.username.contains(keyword))
        return query.count()

    @staticmethod
    def update_user(db: Session, user_id: int, user_in: UserUpdate) -> User:
        """更新用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        update_data = user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """删除用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        db.delete(user)
        db.commit()
        return True
