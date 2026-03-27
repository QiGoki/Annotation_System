"""
项目管理 API 测试
"""
import pytest
from app.core.security import get_password_hash
from app.models.user import User
from app.models.project import Project


def test_create_project(client):
    """测试创建项目"""
    c, db = client

    # 创建用户
    user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()

    # 登录
    login_response = c.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    # 创建项目
    headers = {"Authorization": f"Bearer {token}"}
    response = c.post("/api/v1/projects", headers=headers, json={
        "name": "测试项目",
        "description": "这是一个测试项目",
        "config_json": {
            "version": "1.0",
            "components": [
                {
                    "id": "rect_1",
                    "type": "image_rect",
                    "label": "标注目标",
                    "required": True
                }
            ]
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试项目"
    assert data["description"] == "这是一个测试项目"


def test_get_projects(client):
    """测试获取项目列表"""
    c, db = client

    user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()

    login_response = c.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = c.get("/api/v1/projects", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_project_detail(client):
    """测试获取项目详情"""
    c, db = client

    user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()

    project = Project(
        name="测试项目",
        description="测试描述",
        config_json={"version": "1.0", "components": []},
        created_by=user.id
    )
    db.add(project)
    db.commit()

    login_response = c.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = c.get(f"/api/v1/projects/{project.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试项目"


def test_delete_project(client):
    """测试删除项目"""
    c, db = client

    user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()

    project = Project(
        name="测试项目",
        description="测试描述",
        config_json={"version": "1.0", "components": []},
        created_by=user.id
    )
    db.add(project)
    db.commit()

    login_response = c.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = c.delete(f"/api/v1/projects/{project.id}", headers=headers)

    assert response.status_code == 200
