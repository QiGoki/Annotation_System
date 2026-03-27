# 测试运行指南

## 后端测试

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### 测试用例
- `test_auth.py` - 认证 API 测试（4 个用例）
- `test_users.py` - 用户管理 API 测试（4 个用例）
- `test_projects.py` - 项目管理 API 测试（4 个用例）

## 前端测试

```bash
cd frontend
npm install
npm run test
```

### 测试用例
- `user.test.ts` - 用户 API 测试
- `ImageRect.test.ts` - ImageRect 组件测试

### 测试命令

| 命令 | 说明 |
|------|------|
| `npm run test` | 运行测试 |
| `npm run test:ui` | 带 UI 界面运行测试 |
| `npm run test:coverage` | 生成覆盖率报告 |

## 覆盖率要求

- 后端：> 80%
- 前端：> 70%
