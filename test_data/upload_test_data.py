#!/usr/bin/env python3
"""
测试数据上传脚本
用于将测试数据上传到指定项目
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def login(username: str = "admin", password: str = "admin123") -> str:
    """登录并获取 token"""
    url = f"{BASE_URL}/api/v1/auth/login"
    response = requests.post(url, json={"username": username, "password": password})
    response.raise_for_status()
    data = response.json()
    return data["access_token"]

def get_projects(token: str) -> list:
    """获取项目列表"""
    url = f"{BASE_URL}/api/v1/projects"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def upload_data(token: str, project_id: int, file_path: str) -> dict:
    """上传数据到项目"""
    url = f"{BASE_URL}/api/v1/export/import"
    headers = {"Authorization": f"Bearer {token}"}

    with open(file_path, 'rb') as f:
        files = {"file": (file_path, f)}
        params = {"project_id": project_id}
        response = requests.post(url, headers=headers, files=files, params=params)
        response.raise_for_status()
        return response.json()

def main():
    if len(sys.argv) < 2:
        print("用法：python upload_test_data.py <file_path> [project_id]")
        print("示例：python upload_test_data.py test_data/sample_images.jsonl 1")
        sys.exit(1)

    file_path = sys.argv[1]
    project_id = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print("=" * 50)
    print("测试数据上传工具")
    print("=" * 50)

    # 登录
    print("\n[1/4] 登录...")
    try:
        token = login()
        print("      登录成功！")
    except Exception as e:
        print(f"      登录失败：{e}")
        sys.exit(1)

    # 获取项目列表
    print("\n[2/4] 获取项目列表...")
    try:
        projects = get_projects(token)
        if not projects:
            print("      没有找到项目，请先创建一个项目")
            sys.exit(1)

        print(f"      找到 {len(projects)} 个项目:")
        for i, proj in enumerate(projects, 1):
            print(f"      [{i}] {proj['name']} (ID: {proj['id']}, 任务数：{proj['task_count']})")

        if project_id is None:
            if len(projects) == 1:
                project_id = projects[0]["id"]
                print(f"      自动选择项目：{projects[0]['name']}")
            else:
                choice = input("\n      请选择项目 ID (输入数字): ")
                try:
                    project_id = int(choice)
                except ValueError:
                    print("      无效的输入")
                    sys.exit(1)
    except Exception as e:
        print(f"      获取项目失败：{e}")
        sys.exit(1)

    # 上传数据
    print(f"\n[3/4] 上传文件：{file_path}")
    try:
        result = upload_data(token, project_id, file_path)
        message = result.get("message", result.get("detail", "上传成功"))
        print(f"      {message}")
        # 兼容多种返回格式
        if "created" in result:
            print(f"      创建任务数：{result['created']}")
        elif "count" in result:
            print(f"      创建任务数：{result['count']}")
    except Exception as e:
        print(f"      上传失败：{e}")
        sys.exit(1)

    # 验证结果
    print("\n[4/4] 验证上传结果...")
    try:
        projects = get_projects(token)
        for proj in projects:
            if proj["id"] == project_id:
                print(f"      项目 '{proj['name']}' 现在包含 {proj['task_count']} 个任务")
                break
    except Exception as e:
        print(f"      验证失败：{e}")

    print("\n" + "=" * 50)
    print("上传完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
