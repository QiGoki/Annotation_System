"""
测试包初始化

必须在任何其他模块导入之前设置 TESTING 环境变量
确保 database.py 等模块能正确检测到测试环境
"""
import os
os.environ["TESTING"] = "true"
