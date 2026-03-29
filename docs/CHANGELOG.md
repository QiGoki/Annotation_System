# 开发日志 2026-03-30

## 今日完成

### 1. ImageBBoxAnnotator 组件重构

**文件：** `frontend/src/components/annotation/ImageBBoxAnnotator.vue`

- 重构为使用 `useAnnotationContext` 共享状态
- 支持树形结构 BBox（通过 `childrenField` 配置）
- 实现属性编辑、添加、删除功能
- 支持画布拖拽绘制和调整 BBox

### 2. AnnotationContext 状态管理

**文件：** `frontend/src/composables/useAnnotationContext.ts`

- 创建 Vue 3 provide/inject 模式的状态管理
- 实现 BBox 数据解析（支持 list 和 string 模式）
- 实现树形数据的增删改操作
- 支持 path-based 的节点定位

### 3. BboxPropertyEditor 属性编辑器

**文件：** `frontend/src/components/annotation/BboxPropertyEditor.vue`

- 树形展示 BBox 结构
- 支持拖拽排序
- 支持拖入成为子节点
- 使用 path-based 展开状态追踪（修复 ID-based 导致的展开状态丢失）

### 4. 任务导入逻辑修正

**问题：** 之前每条 JSON 数据创建一个 Task，现在改为每个 JSONL 文件创建一个 Task。

**修改文件：**
- `backend/app/models/task.py` - 添加 `name` 字段
- `backend/app/schemas/task.py` - 更新 schema
- `backend/app/utils/import_utils.py` - 修改导入逻辑
- `backend/app/api/v1/export.py` - 传递文件名

### 5. 批量数据导入

**文件：** `frontend/src/views/task/TaskImport.vue`

- 支持多文件选择和拖拽
- 显示文件列表（带大小）
- 导入进度显示
- 导入结果展示（成功/失败）

### 6. 布局配置保存修复

**问题：** 预览页面点击"保存布局"后，配置丢失。

**原因：** `sessionStorage` 不跨标签页共享，预览是用 `window.open('_blank')` 打开的新标签页。

**修复：**
- `ProjectConfigurator.vue` - 改用 `localStorage`
- `AnnotationRunner.vue` - 改用 `localStorage`

### 7. 任务列表显示优化

**文件：** `frontend/src/views/task/TaskList.vue`

- 显示任务名称（文件名）
- 显示数据数量（`data_source.length`）

## Bug 修复

1. **BBox 删除后消失** - 修复 `deleteBbox` 从 `rawData` 删除而非仅从 `bboxList` 删除
2. **树形展开状态丢失** - 改用 path-based 追踪而非 ID-based
3. **无法将节点拖为子节点** - 移除 `hasChildren` 限制条件
4. **表单区域异常光标** - 添加 `user-select: none` 到非输入区域
5. **保存布局失败** - sessionStorage → localStorage

## 测试数据

创建了两个测试 JSONL 文件：
- `test_task_batch_1.jsonl` - 10条数据（001-010）
- `test_task_batch_2.jsonl` - 10条数据（011-020）

每条数据包含：id, image, text, components（带 bbox）, label, note

## 待解决问题

1. **幽灵组件问题** - 删除画布组件后可能出现残留元素（vuedraggable clone 模式）
2. **ModuleConfigEditor 完善** - 配置表单渲染需要完善
3. **showIf 条件显示** - Schema 的条件显示支持

## 数据库变更

新增字段：`tasks.name` (VARCHAR 255)

如需应用变更：
```sql
DROP TABLE annotations;
DROP TABLE tasks;
-- 然后重启后端，init_db.py 会自动创建新表
```