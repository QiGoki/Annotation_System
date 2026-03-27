"""
用户管理 API 测试
"""
import pytest
from app.core.security import get_password_hash
from app.models.user import User


def test_get_users_list(client):
    """测试获取用户列表（管理员）"""
    c, db = client

    # 创建管理员用户
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()

    # 登录获取 token
    login_response = c.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    # 测试获取用户列表
    headers = {"Authorization": f"Bearer {token}"}
    response = c.get("/api/v1/users", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_users_list_unauthorized(client):
    """测试获取用户列表 - 未授权"""
    c, _ = client

    response = c.get("/api/v1/users")
    assert response.status_code == 401


def test_create_user(client):
    """测试创建用户（管理员）"""
    c, db = client

    # 创建管理员用户
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()

    # 登录获取 token
    login_response = c.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    # 测试创建用户
    headers = {"Authorization": f"Bearer {token}"}
    response = c.post("/api/v1/auth/register", headers=headers, json={
        "username": "newuser",
        "password": "password123",
        "role": "annotator"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "annotator"


def test_create_user_duplicate(client):
    """测试创建用户 - 用户名重复"""
    c, db = client

    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(admin)

    existing_user = User(
        username="existinguser",
        password_hash=get_password_hash("password123"),
        role="annotator",
        is_active=True
    )
    db.add(existing_user)
    db.commit()

    login_response = c.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = c.post("/api/v1/auth/register", headers=headers, json={
        "username": "existinguser",
        "password": "password123",
        "role": "annotator"
    })

    assert response.status_code == 400
