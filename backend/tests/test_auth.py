"""
认证 API 测试
"""
import pytest
from app.core.security import get_password_hash
from app.models.user import User


def test_login_success(client):
    """测试登录成功"""
    c, db = client

    # 创建测试用户
    user = User(
        username="testuser",
        password_hash=get_password_hash("password123"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 测试登录
    response = c.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"


def test_login_wrong_password(client):
    """测试登录 - 密码错误"""
    c, db = client

    user = User(
        username="testuser",
        password_hash=get_password_hash("password123"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()

    response = c.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })

    assert response.status_code == 401


def test_login_user_not_found(client):
    """测试登录 - 用户不存在"""
    c, _ = client

    response = c.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "password123"
    })

    assert response.status_code == 401


def test_login_inactive_user(client):
    """测试登录 - 用户已禁用"""
    c, db = client

    user = User(
        username="disableduser",
        password_hash=get_password_hash("password123"),
        role="admin",
        is_active=False
    )
    db.add(user)
    db.commit()

    response = c.post("/api/v1/auth/login", json={
        "username": "disableduser",
        "password": "password123"
    })

    assert response.status_code == 403
