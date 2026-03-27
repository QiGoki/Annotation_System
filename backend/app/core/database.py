"""
数据库连接配置
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 检测是否在测试环境（支持 pytest 运行时）
IS_TESTING = os.getenv("TESTING") == "true" or 'pytest' in sys.modules

if IS_TESTING:
    # 使用临时文件数据库而不是 :memory:，因为 SQLite 的 :memory: 在每个新连接时都会重新创建
    import tempfile
    _temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    _temp_db_path = _temp_db.name
    _temp_db.close()
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{_temp_db_path}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # 创建数据库引擎
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,  # 连接前 ping 测试
        echo=settings.DEBUG,  # 开发环境打印 SQL
    )

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# 测试环境清理函数
def cleanup_test_db():
    """清理测试数据库文件"""
    if IS_TESTING and '_temp_db_path' in globals():
        try:
            import os
            os.unlink(_temp_db_path)
        except Exception:
            pass


def get_db():
    """获取数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
