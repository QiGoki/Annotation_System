# 多模态混合标注低代码平台

一个支持多种标注类型的低代码平台，用户可以通过可视化配置快速搭建标注工作流，无需编写代码。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | MySQL |
| UI风格 | StepFun/阶跃星辰风格 |

## 项目结构

```
Annotation_System/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   │   ├── auth.py        # 认证接口
│   │   │   ├── projects.py    # 项目管理
│   │   │   ├── tasks.py       # 任务管理
│   │   │   ├── annotations.py # 标注接口
│   │   │   ├── export.py      # 数据导入导出
│   │   │   └── project_members.py # 项目成员
│   │   ├── models/            # 数据模型
│   │   │   ├── user.py        # 用户模型
│   │   │   ├── project.py     # 项目模型
│   │   │   ├── task.py        # 任务模型
│   │   │   ├── annotation.py  # 标注结果模型
│   │   │   └── project_member.py # 成员关系
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── services/          # 业务逻辑层
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 应用配置
│   │   │   ├── database.py    # 数据库连接
│   │   │   ├── security.py    # JWT/密码
│   │   │   └── deps.py        # 依赖注入
│   │   └── utils/             # 工具函数
│   ├── init_db.py             # 数据库初始化
│   └── requirements.txt
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── project/       # 项目相关页面
│   │   │   │   ├── ProjectConfigurator.vue  # **核心** 配置器页面
│   │   │   ├── annotation/    # 标注相关页面
│   │   │   │   ├── AnnotationRunner.vue    # **核心** 标注执行页面
│   │   │   ├── task/          # 任务相关页面
│   │   │   │   ├── TaskList.vue           # 任务列表
│   │   │   │   ├── TaskImport.vue         # 数据导入
│   │   │   ├── user/          # 用户相关页面
│   │   ├── components/        # 组件
│   │   │   ├── annotation/    # 标注组件
│   │   │   │   ├── ImageBBoxAnnotator.vue # **核心** 图片拉框标注器
│   │   │   │   ├── BboxPropertyEditor.vue # BBox 属性编辑器
│   │   │   │   ├── AnnotationSidebar.vue  # 标注侧边栏
│   │   │   │   ├── LayoutContainer.vue    # 布局容器
│   │   │   │   ├── TextViewer.vue         # 文本查看器
│   │   │   │   ├── RadioSelector.vue      # 单选组件
│   │   │   │   ├── TextInput.vue          # 文本输入
│   │   │   │   ├── ModuleConfigEditor.vue # 模块配置编辑器
│   │   ├── composables/       # 组合式函数
│   │   │   ├── useAnnotationContext.ts    # **核心** 标注上下文状态管理
│   │   │   ├── useAnnotationModuleRegistry.ts # 模块注册表
│   │   │   ├── useDataSourceParser.ts     # 数据源解析器
│   │   │   ├── useAnnotationSidebar.ts    # 侧边栏逻辑
│   │   ├── types/             # 类型定义
│   │   │   ├── annotation-module.ts       # **核心** 模块配置类型
│   │   │   ├── annotation-tool.ts         # 标注工具类型
│   │   │   ├── task.ts                    # 任务类型
│   │   │   ├── project.ts                 # 项目类型
│   │   ├── api/               # API 调用
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态
│   │   └── utils/             # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                       # 详细文档
│   ├── 01-项目概述与技术架构.md
│   ├── 02-数据模型设计.md
│   ├── 03-用户管理模块.md
│   ├── 04-任务管理模块.md
│   ├── 05-低代码标注配置系统.md
│   ├── 06-标注执行模块.md
│   ├── 07-ImageBBoxAnnotator设计方案.md
│   ├── 08-项目问题诊断报告.md
│   └── TASK_CLAIM_MECHANISM.md
│
└── test_data/                  # 测试数据生成脚本
```

## 核心概念

### 1. 模块系统（低代码核心）

平台通过**模块注册表**实现低代码配置：

```typescript
// frontend/src/composables/useAnnotationModuleRegistry.ts

// 模块定义
interface ModuleDefinition {
  id: string              // 模块ID，如 'ImageBBoxAnnotator'
  name: string            // 显示名称
  icon: string            // 图标
  description?: string    // 描述
  component: any          // Vue组件
  configSchema?: Record<string, ConfigFieldSchema>  // 配置表单Schema
  defaultConfig?: any     // 默认配置
}

// 已注册模块
- ImageBBoxAnnotator  // 图片拉框标注器
- TextViewer          // 文本查看器
- RadioSelector       // 单选组件
- TextInput           // 文本输入组件
```

### 2. AnnotationContext（状态共享）

使用 Vue 3 的 provide/inject 实现跨组件状态共享：

```typescript
// frontend/src/composables/useAnnotationContext.ts

interface AnnotationContext {
  rawData: Ref<any>                    // 当前数据项
  config: Ref<ImageBBoxAnnotatorConfig> // 模块配置
  bboxList: Ref<BboxItem[]>            // BBox列表
  selectedId: Ref<string | null>       // 选中的BBox ID

  // 方法
  setRawData(data: any): void          // 设置数据
  parseBboxList(): void                // 解析BBox
  updateBbox(id, field, value): void   // 更新属性
  addBbox(bbox, parentPath): void      // 添加BBox
  deleteBbox(id): void                 // 删除BBox
  getOutputData(): any[]               // 获取输出数据
}
```

### 3. 配置Schema系统

支持动态渲染配置表单：

```typescript
// frontend/src/types/annotation-module.ts

type ConfigFieldSchema =
  | { type: 'string', label: string, default?: string }
  | { type: 'number', label: string, default?: number }
  | { type: 'boolean', label: string, default?: boolean }
  | { type: 'select', label: string, options: string[] }
  | { type: 'field-select', label: string }  // 从数据字段选择
  | { type: 'group', label: string, fields: Record<string, ConfigFieldSchema> }
  | { type: 'array', label: string, itemSchema: Record<string, ConfigFieldSchema> }
  | { type: 'array-string', label: string }  // 字符串数组
```

### 4. 任务数据模型

```
Project (项目)
  ├── config_json      // 页面配置（模块、布局）
  ├── members          // 项目成员
  └── tasks            // 任务列表
        ├── name       // 任务名称（文件名）
        ├── data_source // 数据数组（JSONL内容）
        ├── status     // pending/doing/completed
        ├── assigned_to // 领取人
        └── annotation // 标注结果
```

**重要概念：一个JSONL文件 = 一个Task**
- 导入时，整个JSONL文件内容存入 `Task.data_source` 数组
- 任务名称取文件名（去除扩展名）
- 标注时遍历 `data_source` 中的每条数据

## 工作流程

### 配置流程（ProjectConfigurator）

```
1. 上传示例JSON → 解析字段 → 存入 parsedFields
2. 从模块市场拖拽组件到画布
3. 配置组件参数（通过 ModuleConfigEditor）
4. 点击"测试" → 打开预览页面（localStorage传递配置）
5. 点击"保存布局" → 保存到后端
```

### 标注流程（AnnotationRunner）

```
1. 领取任务 → 任务状态变为 doing
2. 加载 Task.data_source 数组
3. 加载页面配置（模块、布局）
4. 遍历数据项，使用配置的组件进行标注
5. 保存 → 写入 Annotation.result_json
6. 提交 → 任务状态变为 completed
```

## 最近完成的开发（2026-03-30）

### 已完成

1. **ImageBBoxAnnotator 重构**
   - 使用 AnnotationContext 共享状态
   - 支持树形结构 BBox（childrenField）
   - 支持属性编辑、添加、删除、拖拽排序

2. **任务导入逻辑修正**
   - 一个JSONL文件创建一个Task（之前是每条数据一个Task）
   - Task.name 存储文件名
   - Task.data_source 存储数据数组

3. **批量数据导入**
   - TaskImport.vue 支持多文件上传
   - 显示导入进度和结果

4. **布局配置保存**
   - 支持"平铺"模式切换
   - 左列宽度可调整并保存
   - 预览模式用 localStorage，任务模式保存到后端

5. **BboxPropertyEditor**
   - 树形展示 BBox
   - 支持拖拽排序、拖入成为子节点
   - path-based 展开状态追踪

### 待完成/问题

1. **配置面板UI完善**
   - ModuleConfigEditor 需要完善渲染
   - showIf 条件显示支持

2. **幽灵组件问题**
   - 删除画布组件后可能出现残留元素
   - vuedraggable clone 模式问题

3. **导出功能**
   - 批量导出标注结果
   - 支持多种格式

4. **性能优化**
   - 大数据量加载优化
   - 图片加载优化

## 数据库表结构

```sql
-- 用户表
users (id, username, password_hash, role, is_active, created_at)

-- 项目表
projects (id, name, description, config_json, created_by, created_at)

-- 项目成员表
project_members (id, project_id, user_id, role, joined_at)

-- 任务表
tasks (id, project_id, name, data_source[JSON], status, assigned_to, created_at, completed_at)

-- 标注结果表
annotations (id, task_id, result_json, created_by, created_at, updated_at)
```

## API 路由

```
认证
POST /api/v1/auth/login    # 登录
POST /api/v1/auth/register # 注册（仅管理员）

用户管理
GET  /api/v1/users         # 用户列表
POST /api/v1/users         # 创建用户
PUT  /api/v1/users/{id}    # 更新用户

项目管理
GET  /api/v1/projects      # 项目列表
POST /api/v1/projects      # 创建项目
GET  /api/v1/projects/{id} # 项目详情
PUT  /api/v1/projects/{id} # 更新项目
GET  /api/v1/projects/{id}/page-config # 获取标注页面配置
POST /api/v1/projects/{id}/page-config # 保存标注页面配置

任务管理
GET  /api/v1/tasks         # 任务列表
GET  /api/v1/tasks/{id}    # 任务详情
POST /api/v1/tasks/{id}/claim   # 领取任务
POST /api/v1/tasks/{id}/release # 释放任务
POST /api/v1/tasks/{id}/annotate # 保存标注
POST /api/v1/tasks/{id}/submit  # 提交任务

数据导入导出
POST /api/v1/export/import        # 导入JSONL
GET  /api/v1/export/export        # 导出结果
```

## UI 风格（StepFun风格）

```
主色调：#165DFF（蓝色）
背景色：#F9FAFB（浅灰）
边框色：#E5E7EB
文字色：#111827（主）、#6B7280（次）

按钮风格：
- 主按钮：蓝色背景，白色文字
- 次按钮：浅灰背景，深灰文字
- 禁用：灰底灰字

卡片风格：
- 白色背景，12px圆角
- 1px浅灰边框
- 内边距16px

表单风格：
- 输入框：浅灰背景，8px圆角
- select：200px宽度
- 标签：13px，深灰色
```

## 启动方式

```bash
# 后端（需要MySQL）
cd backend
pip install -r requirements.txt
python init_db.py  # 初始化数据库
python -m uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev  # 端口 5173
```

## 默认账号

- 管理员：admin / admin123

## 注意事项

1. **前后端重启由用户维护** - 修改代码后需要手动重启服务
2. **数据库模型变更** - 需要执行 DROP TABLE 后重新 init_db.py
3. **sessionStorage vs localStorage**
   - 预览配置用 localStorage（跨标签页）
   - 用户偏好用 localStorage
   - 页面配置保存到后端

## 联系与维护

此项目为多模态标注平台原型，核心功能已实现约95%，可继续扩展更多标注类型和优化用户体验。