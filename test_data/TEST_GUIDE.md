# 标注平台测试指南

## 测试数据说明

当前系统已创建以下测试数据：

### 测试数据文件

| 文件 | 类型 | 记录数 | 描述 |
|------|------|--------|------|
| `test_data/images_direct.jsonl` | 图像 | 8 | 图像标注测试（正确格式） |
| `test_data/texts_direct.jsonl` | 文本 | 6 | 文本标注测试（正确格式） |
| `test_data/sample_images.jsonl` | 图像 | 5 | 旧格式（嵌套 data_source） |
| `test_data/sample_texts.jsonl` | 文本 | 6 | 旧格式（嵌套 data_source） |

### 数据格式

**推荐格式**（直接包含 data_source 字段内容）:
```jsonl
{"type": "image", "url": "https://example.com/img.jpg", "filename": "test.jpg"}
{"type": "text", "content": "这是文本内容"}
```

### 当前数据库状态

- **项目**: 测试项目 (ID: 1)
- **任务总数**: 20 个
- **任务类型**: 图像 (14 个) + 文本 (6 个)
- **所有状态**: pending (待标注)

---

## 测试步骤

### 步骤 1：登录系统

访问 http://localhost:5173/login
- 账号：`admin`
- 密码：`admin123`

### 步骤 2：查看项目

访问 http://localhost:5173/projects
- 点击"测试项目"查看详情
- 可以看到 20 个任务的列表

### 步骤 3：标注任务

1. 访问 http://localhost:5173/tasks 查看待标注任务
2. 点击"开始标注"进入标注页面
3. 测试图像或文本标注功能

### 步骤 4：测试上传功能

```bash
cd /home/goki/annotation-platform

# 上传新的测试数据
python test_data/upload_test_data.py test_data/texts_direct.jsonl 1
```

### 步骤 5：测试导出功能

```bash
# 导出标注结果为 JSONL
curl -o exported_data.jsonl \
  "http://localhost:8000/api/v1/export/export?project_id=1&format=jsonl" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 测试用例

### 1. 用户管理测试
- [ ] 创建新用户
- [ ] 修改用户角色
- [ ] 禁用/启用用户
- [ ] 删除用户

### 2. 项目管理测试
- [ ] 创建新项目
- [ ] 编辑项目配置
- [ ] 删除项目
- [ ] 查看项目统计

### 3. 数据导入测试
- [ ] 上传 JSONL 文件
- [ ] 上传 JSON 文件
- [ ] 验证错误格式文件处理

### 4. 标注功能测试
- [ ] 图像标注（矩形框）
- [ ] 图像分类
- [ ] 文本标注
- [ ] 文本分类
- [ ] 保存标注
- [ ] 提交标注

### 5. 导航功能测试
- [ ] 上一条/下一条切换
- [ ] 快捷键操作（Ctrl+S, Ctrl+Enter）
- [ ] 自动保存功能

---

## API 测试

### 获取 Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
```

### 获取待标注任务
```bash
curl -s http://localhost:8000/api/v1/tasks/pending \
  -H "Authorization: Bearer $TOKEN"
```

### 获取任务详情
```bash
curl -s http://localhost:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 保存标注
```bash
curl -s -X POST http://localhost:8000/api/v1/annotate/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"result_json": {"category": "cat", "boxes": []}}'
```

### 提交标注
```bash
curl -s -X POST http://localhost:8000/api/v1/annotate/1/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"result_json": {"category": "cat", "boxes": []}}'
```

---

## 故障排除

### 问题：上传数据后任务数为 0
- 检查 JSONL 文件格式是否正确
- 确保每行是完整的 JSON 对象
- 确保包含 `type` 字段（image 或 text）

### 问题：无法连接数据库
- 确认 MySQL 服务运行
- 检查 backend/.env 中的数据库配置
- 确认数据库 annotation_platform 存在

### 问题：前端无法访问后端
- 确认后端服务运行在端口 8000
- 检查 frontend/vite.config.ts 中的代理配置
- 清除浏览器缓存

---

## 快速重置测试环境

```bash
# 1. 清空任务表（保留项目）
cd /home/goki/annotation-platform/backend
source venv/bin/activate

python -c "
from app.core.database import SessionLocal
from app.models.task import Task
from app.models.annotation import Annotation
db = SessionLocal()
db.query(Annotation).delete()
db.query(Task).delete()
db.commit()
print('已清空任务和标注数据')
db.close()
"

# 2. 重新上传测试数据
cd ..
python test_data/upload_test_data.py test_data/images_direct.jsonl 1
python test_data/upload_test_data.py test_data/texts_direct.jsonl 1
```
