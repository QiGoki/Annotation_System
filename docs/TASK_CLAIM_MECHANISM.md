# 任务领取机制实现文档

## 核心设计

### 数据模型

#### 1. ProjectMember 表
```sql
CREATE TABLE project_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,          -- 项目 ID
    user_id INT NOT NULL,             -- 用户 ID
    role VARCHAR(20) DEFAULT 'member', -- admin | member
    joined_at DATETIME,
    UNIQUE KEY uq_project_user (project_id, user_id)
);
```

#### 2. Task 表状态
```
pending  -> 待领取（未分配）
doing    -> 已领取（标注中）
completed -> 已完成
```

---

## 权限控制

### 项目层级
| 操作 | 权限 |
|------|------|
| 创建项目 | 管理员 |
| 添加/移除成员 | 项目创建者或系统管理员 |
| 查看成员列表 | 项目成员 |
| 查看项目任务 | 项目成员 |

### 任务层级
| 操作 | 权限 |
|------|------|
| 领取任务 | 项目成员 |
| 释放任务 | 任务领取者或项目管理员 |
| 标注任务 | 任务领取者 |

---

## API 端点

### 项目成员管理
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/project-members/my-projects` | 获取我的项目列表 |
| GET | `/api/v1/project-members/{id}/members` | 获取项目成员 |
| POST | `/api/v1/project-members/{id}/members` | 添加成员 |
| DELETE | `/api/v1/project-members/{id}/members/{uid}` | 移除成员 |
| PUT | `/api/v1/project-members/{id}/members/{uid}/role` | 更新角色 |

### 任务领取
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/tasks/{id}/claim` | 领取任务 |
| POST | `/api/v1/tasks/{id}/release` | 释放任务 |

---

## 业务流程

### 1. 项目创建与成员分配
```
管理员创建项目
    ↓
添加项目成员（设置角色）
    ↓
成员可以看到"我的项目"中的项目
```

### 2. 任务领取流程
```
成员登录
    ↓
访问"我的任务"页面
    ↓
选择项目，查看任务列表
    ↓
点击"领取"按钮（pending -> doing）
    ↓
任务被标记为"已领取"，其他人不可再领
    ↓
点击"标注"开始标注
    ↓
保存/提交标注（doing -> completed）
```

### 3. 任务释放流程
```
任务领取者或管理员
    ↓
点击"释放"按钮
    ↓
任务状态变回 pending
    ↓
其他成员可以领取
```

---

## 关键约束

1. **独占性**: 同一任务同一时间只能被 1 人领取
2. **成员可见**: 只有项目成员能看见项目及任务
3. **无需审批**: 项目成员分配即代表授权
4. **状态转换**:
   - `pending` → `doing` (领取)
   - `doing` → `completed` (提交)
   - `doing` → `pending` (释放)

---

## 后端实现

### 服务层
- `ProjectMemberService`: 项目成员管理
- `ClaimTaskService`: 任务领取管理

### 核心逻辑
```python
# 领取任务
def claim_task(task_id, user_id):
    task = get_task(task_id)

    # 检查任务状态
    if task.status != "pending":
        raise ValueError("任务不可领取")

    # 检查成员资格
    if not is_member(project_id, user_id):
        raise ValueError("非项目成员")

    # 领取
    task.assigned_to = user_id
    task.status = "doing"
    return task
```

---

## 前端实现

### 新增页面
- `MyTasks.vue`: 我的任务页面（任务领取入口）

### 新增 API
- `project_members.ts`: 项目成员管理 API
- `task.ts`: 新增 `claimTask`, `releaseTask`

### 路由
```typescript
{
  path: '/my-tasks',
  name: 'MyTasks',
  component: () => import('@/views/task/MyTasks.vue')
}
```

---

## 测试验证

### 1. 领取任务测试
```bash
# 领取成功
POST /api/v1/tasks/14/claim
响应：{"code":200,"message":"领取成功","data":{"status":"doing"}}

# 重复领取（失败）
POST /api/v1/tasks/14/claim
响应：{"detail":"任务已被领取，当前标注中"}
```

### 2. 非成员领取（失败）
```bash
# 创建新用户并尝试领取
# 响应：{"detail":"您不是该项目成员，无法领取任务"}
```

### 3. 释放任务
```bash
POST /api/v1/tasks/14/release
响应：{"code":200,"message":"释放成功","data":{"status":"pending"}}
```

---

## 待办事项

1. [ ] 前端用户选择器（添加项目成员时）
2. [ ] 项目详情页显示成员列表
3. [ ] 任务列表页显示领取人信息
4. [ ] 释放任务的二次确认对话框
5. [ ] 任务统计（按成员）

---

## 快速测试

```bash
# 1. 访问我的任务页面
http://localhost:5173/my-tasks

# 2. 选择项目
# 3. 点击"领取"按钮
# 4. 验证任务状态变更
```
