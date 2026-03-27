# 标注平台

多模态混合标注低代码平台

## 技术栈

### 后端
- FastAPI 0.109+
- Python 3.10+
- SQLAlchemy 2.x
- PostgreSQL 15+
- JWT 认证
- bcrypt 密码加密

### 前端
- Vue 3.4+
- TypeScript 5.x
- Element Plus 2.x
- Pinia 2.x
- Vue Router 4.x
- Vite 5.x

## 项目结构

```
annotation-platform/
├── backend/                 # 后端项目
│   ├── app/
│   │   ├── api/v1/         # API 路由
│   │   │   ├── auth.py     # 认证接口
│   │   │   ├── users.py    # 用户管理接口
│   │   │   ├── projects.py # 项目管理接口
│   │   │   ├── tasks.py    # 任务管理接口
│   │   │   ├── annotations.py # 标注执行接口
│   │   │   └── export.py   # 数据导出接口
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py   # 应用配置
│   │   │   ├── database.py # 数据库连接
│   │   │   ├── security.py # 安全工具
│   │   │   └── deps.py     # 依赖注入
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic Schema
│   │   ├── services/       # 业务服务
│   │   └── main.py         # 应用入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # 前端项目
│   ├── src/
│   │   ├── api/           # API 调用
│   │   ├── assets/        # 静态资源
│   │   ├── components/    # 公共组件
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── types/         # TypeScript 类型
│   │   ├── utils/         # 工具函数
│   │   ├── views/         # 页面组件
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
└── docs/                  # 项目文档
```

## 快速开始

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp .env.example .env

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 默认账号

- 管理员：admin / admin123

## API 文档

启动后端后访问：http://localhost:8000/docs

## 功能特性

### 用户管理
- 用户注册/登录/登出
- 密码修改
- 用户列表查询（管理员）
- 启用/禁用用户（管理员）

### 项目管理
- 创建/编辑/删除项目
- 低代码标注配置
- 数据导入（JSON/JSONL）
- 标注结果导出
- 进度统计

### 标注执行
- 动态渲染标注组件
- 图像标注（矩形框、分类）
- 文本标注（分类、NER、输入）
- 自动保存
- 快捷键支持

## 开发进度

- [x] 后端基础框架
- [x] 数据库模型
- [x] 用户管理 API
- [x] 项目管理 API
- [x] 任务管理 API
- [x] 标注执行 API
- [x] 前端基础框架
- [x] 登录页面
- [x] 用户管理页面
- [x] 项目管理页面
- [x] 低代码配置器
- [x] 标注执行页面
- [x] 数据导入页面

## 待完成功能

- [ ] 完整的图像矩形框标注交互（Canvas）
- [ ] 文本实体标注交互
- [ ] 多边形标注
- [ ] 批量分配任务
- [ ] 数据导出功能完善
- [ ] Docker 部署配置
- [ ] 单元测试
