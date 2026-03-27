"""
测试配置

注意：必须在导入任何 app 模块之前设置 TESTING 环境变量
"""
import os
import sys

# 设置测试环境变量（必须在导入 app 之前）
os.environ["TESTING"] = "true"

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from starlette.testclient import TestClient

from app.core.database import get_db, Base, engine, SessionLocal

# 导入所有模型以注册到 Base.metadata（必须在 create_all 之前）
from app.models import user, project, task, annotation

from app.main import app


@pytest.fixture(scope="function")
def client():
    """创建测试客户端"""
    # 创建表
    Base.metadata.create_all(bind=engine)

    # 创建 session
    db = SessionLocal()

    # 设置 override
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # 创建测试客户端
    with TestClient(app) as c:
        yield c, db

    # 清理
    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

    # 清理测试数据库文件
    from app.core.database import cleanup_test_db
    cleanup_test_db()
