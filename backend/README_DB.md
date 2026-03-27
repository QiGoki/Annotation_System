# 标注平台后端 - 数据库配置指南

## MySQL 数据库配置

### 1. 环境准备

确保你的本地环境已安装 MySQL 服务。

### 2. 创建数据库

```sql
CREATE DATABASE annotation_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置环境变量

编辑 `backend/.env` 文件，配置 MySQL 连接：

```bash
# 数据库配置 (MySQL)
# 格式：mysql+pymysql://用户名：密码@主机：端口/数据库名？charset=utf8mb4
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/annotation_platform?charset=utf8mb4
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 应用配置
DEBUG=true
```

**注意：** 如果密码中包含特殊字符（如 `@`, `#`, `$` 等），需要进行 URL 编码：
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- 空格 → `%20`

### 4. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 5. 初始化数据库

运行初始化脚本创建表和初始管理员账号：

```bash
python init_db.py
```

成功后会看到：
```
数据库表创建成功!
初始管理员账号创建成功!
  用户名：admin
  密码：admin123
  角色：管理员
```

### 6. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 7. 验证

```bash
# 测试登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## API 测试

### 创建用户（需要管理员权限）

```bash
TOKEN="你的 access_token"

curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":"testuser","password":"test123","role":"annotator"}'
```

### 创建项目

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"测试项目","description":"测试","config_json":{"version":"1.0","components":[]}}'
```

### 上传数据

```bash
# 创建测试数据文件
echo '[{"url":"http://example.com/image1.jpg"}]' > test_data.json

curl -X POST "http://localhost:8000/api/v1/export/import?project_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_data.json"
```

## 常见问题

### 1. 密码包含特殊字符

如果 MySQL 密码包含 `@` 等特殊字符，需要 URL 编码：
```bash
# 错误示例（密码是 S@z464）
DATABASE_URL=mysql+pymysql://root:S@z464@localhost:3306/annotation_platform

# 正确示例（@编码为%40）
DATABASE_URL=mysql+pymysql://root:S%40z464@localhost:3306/annotation_platform
```

### 2. 连接被拒绝

检查 MySQL 服务是否运行：
```bash
# Linux/Mac
mysql.server status

# Windows
net start MySQL
```

### 3. 数据库不存在

确保已创建数据库：
```sql
SHOW DATABASES;
-- 如果没有 annotation_platform，执行创建
CREATE DATABASE annotation_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
