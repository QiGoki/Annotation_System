#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库、表和初始管理员账号

使用方法:
    python init_db.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.annotation import Annotation
from app.models.project_member import ProjectMember


def init_database():
    """初始化数据库"""
    print("正在创建数据库表...")

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功!")

    # 创建初始管理员账号
    db = SessionLocal()
    try:
        # 检查是否已存在管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("管理员账号已存在，跳过创建")
        else:
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            print("初始管理员账号创建成功!")
            print("  用户名：admin")
            print("  密码：admin123")
            print("  角色：管理员")
    except Exception as e:
        db.rollback()
        print(f"创建管理员账号失败：{e}")
        raise
    finally:
        db.close()

    print("\n数据库初始化完成!")


if __name__ == "__main__":
    init_database()
