# 测试数据总结

## 已创建的文件

### 1. 测试数据文件

| 文件 | 类型 | 记录数 | 状态 |
|------|------|--------|------|
| `test_data/images_direct.jsonl` | 图像 | 8 | 已上传 |
| `test_data/texts_direct.jsonl` | 文本 | 6 | 已上传 |
| `test_data/sample_images.jsonl` | 图像 | 5 | 已上传 (旧格式) |
| `test_data/sample_texts.jsonl` | 文本 | 6 | 已上传 (旧格式) |
| `test_data/sample_images.json` | 图像 | 8 | 未上传 |

### 2. 工具文件

| 文件 | 描述 |
|------|------|
| `test_data/upload_test_data.py` | Python 上传脚本 |
| `test_data/README.md` | 测试数据说明 |
| `test_data/TEST_GUIDE.md` | 完整测试指南 |

## 当前系统状态

**数据库**: MySQL (annotation_platform)
**项目**: 测试项目 (ID: 1)
**任务总数**: 20 个
- 图像任务：14 个
- 文本任务：6 个

**任务状态分布**:
- pending: 19 个
- completed: 1 个 (任务 13，已测试标注)

## 测试结果

### API 功能测试

| 功能 | 端点 | 状态 |
|------|------|------|
| 登录 | POST /api/v1/auth/login | 正常 |
| 获取项目列表 | GET /api/v1/projects | 正常 |
| **获取任务列表** | **GET /api/v1/tasks?project_id={id}** | **正常 (新增)** |
| 数据导入 | POST /api/v1/export/import | 正常 |
| 获取任务详情 | GET /api/v1/tasks/{id} | 正常 |
| 获取下一个任务 | GET /api/v1/tasks/{id}/next | 正常 |
| 保存标注 | POST /api/v1/tasks/{id}/annotate | 正常 |
| 提交标注 | POST /api/v1/tasks/{id}/submit | 正常 |

### 前端功能测试

| 功能 | 状态 |
|------|------|
| 用户登录 | 正常 |
| 项目列表 | 正常 |
| 数据导入 | 正常 |
| 标注执行 | 正常 |
| 表单验证 | 正常 |
| 错误提示 | 正常 |

## 快速测试命令

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# 2. 查看任务列表
curl -s "http://localhost:8000/api/v1/tasks/13" -H "Authorization: Bearer $TOKEN"

# 3. 测试标注
curl -s -X POST "http://localhost:8000/api/v1/tasks/14/annotate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"result_json": {"category": "test"}}'

# 4. 提交标注
curl -s -X POST "http://localhost:8000/api/v1/tasks/14/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"result_json": {"category": "test"}}'

# 5. 上传新测试数据
cd /home/goki/annotation-platform
python test_data/upload_test_data.py test_data/texts_direct.jsonl 1
```

## 验证标注结果

```bash
# 查看任务 13 的标注结果
curl -s "http://localhost:8000/api/v1/tasks/13" -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('状态:', d['status']); print('标注:', d.get('annotation', '无'))"
```

## 下一步

1. 访问前端测试：http://localhost:5173
2. 使用 admin/admin123 登录
3. 进入标注页面测试图像/文本标注
4. 测试快捷键（Ctrl+S 保存，Ctrl+Enter 提交）
5. 测试上一条/下一条导航
