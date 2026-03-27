# 标注平台运行状态

## 服务状态

| 服务 | 状态 | 地址 |
|------|------|------|
| 后端 API | 正常运行 | http://localhost:8000 |
| 前端服务 | 正常运行 | http://localhost:5173 |
| MySQL 数据库 | 正常连接 | localhost:3306/annotation_platform |

## 数据库信息

- **用户数**: 2 (admin, test)
- **项目数**: 1 (测试项目)
- **任务数**: 1

## 登录账号

- **管理员账号**: admin / admin123
- **标注员账号**: test / test123 (如果已创建)

## 已完成配置

### 1. 后端配置 (backend/.env)
```
DATABASE_URL=mysql+pymysql://root:S%40z46415297@localhost:3306/annotation_platform?charset=utf8mb4
```

### 2. 前端代理配置 (frontend/vite.config.ts)
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

### 3. 错误处理完善

所有表单页面已完成错误处理：
- ✅ Login.vue - 登录表单验证 + 错误弹窗
- ✅ UserCreate.vue - 用户创建表单验证 + 详细错误信息
- ✅ UserList.vue - 用户列表操作错误处理
- ✅ ProjectCreate.vue - 项目创建表单验证 + 错误处理
- ✅ ProjectEdit.vue - 项目编辑表单验证 + 错误处理
- ✅ ProjectList.vue - 项目列表操作错误处理
- ✅ TaskImport.vue - 数据导入错误处理
- ✅ AnnotationRunner.vue - 标注保存/提交错误处理

错误处理模式：
```typescript
catch (e: any) {
  let errorMsg = '操作失败'
  if (e.response?.data?.detail) {
    const detail = e.response.data.detail
    if (typeof detail === 'string') {
      errorMsg = detail
    } else if (Array.isArray(detail)) {
      errorMsg = detail.map((err: any) =>
        `${err.loc?.join('.') || '输入'}: ${err.msg || '验证失败'}`
      ).join('; ')
    }
  }
  ElMessage.error(errorMsg)
}
```

## 启动命令

### 后端
```bash
cd /home/goki/annotation-platform/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端
```bash
cd /home/goki/annotation-platform/frontend
npm run dev
```

## 访问地址

- **前端**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **登录页面**: http://localhost:5173/login

## 注意事项

1. 确保 MySQL 服务正在运行
2. 确保数据库 `annotation_platform` 已创建
3. 确保后端虚拟环境已激活
4. 密码中的特殊字符需要 URL 编码（如 @ 编码为 %40）
