# ImageBBoxAnnotator 组件设计方案

> 更新时间：2026-03-27

## 一、组件概述

图片拉框标注器，用于在图片上展示和编辑 bbox，配合属性编辑器修改 bbox 属性。

### 职责边界

| 职责 | 属于 |
|------|------|
| 图片展示 + bbox 框绘制 | ImageBBoxAnnotator |
| 单个 bbox 选中/调整/新建 | ImageBBoxAnnotator |
| bbox 属性编辑 | ImageBBoxAnnotator (BboxPropertyEditor) |
| 树形结构展示 | ComponentTree |
| 层级操作（上移/下移/提级/降级） | ComponentTree |

### 与 ComponentTree 的联动

- 选中状态共享：`selectedId`
- 代表属性共享：`representField`
- bbox 数据共享：`bboxList`
- 修改同步：响应式更新

---

## 二、配置结构

```typescript
interface ImageBBoxAnnotatorConfig {
  // 自定义标题（显示在组件头部）
  title: string

  // 图片设置
  image: {
    field: string                              // JSON 路径，如 "image"
    pathClean?: {
      enabled: boolean
      prefix: string                           // 要清除的路径前缀
    }
  }

  // BBox 数据源
  bboxSource: {
    mode: 'list' | 'conversation'              // 列表模式 or 对话提取模式

    // list 模式
    dataPath?: string                          // 数据路径，如 "items", "annotations"
    bboxField?: string                         // bbox 字段名，默认 "bbox"

    // conversation 模式
    conversationPath?: string                  // 对话字段路径，如 "conversations"
    extractRegex?: string                      // 提取正则，如 "\[(\d+,\s*\d+,\s*\d+,\s*\d+)\]"
  }

  // BBox 属性定义
  bboxProperties: Array<{
    name: string           // 属性标识，如 "type", "text"
    sourceField: string    // 来源字段，如 "type", "content"
    displayName: string    // 显示名称，如 "类型", "文本内容"
    defaultValue?: any     // 新建时的默认值
  }>

  // 代表属性（用于框上显示、区分不同 bbox）
  representField: string   // 如 "type"，必须在 bboxProperties 中存在

  // 输出设置
  output: {
    fields: string[]       // 需要输出的字段名
  }
}
```

---

## 三、共享状态设计

### 3.1 数据结构

```typescript
// 单个 BBox 项
interface BboxItem {
  id: string                                       // 内部唯一 ID
  path: number[]                                   // 在原数据中的路径（用于导出）
  bbox: [number, number, number, number]          // [x1, y1, x2, y2]

  // 动态属性（根据 bboxProperties 配置）
  [key: string]: any
}

// 共享上下文
interface AnnotationContext {
  // 数据
  bboxList: Ref<BboxItem[]>

  // 交互状态
  selectedId: Ref<string | null>
  representField: Ref<string>

  // 计算属性
  selectedBbox: ComputedRef<BboxItem | null>

  // 方法
  updateBbox(id: string, field: string, value: any): void
  addBbox(props: Partial<BboxItem>): void
  deleteBbox(id: string): void
  selectBbox(id: string | null): void
}
```

### 3.2 响应式同步原理

```
用户在 BboxPropertyEditor 修改 type
              │
              ▼
      updateBbox(id, 'type', 'input')
              │
              ▼
        bboxList 响应式更新
              │
    ┌─────────┴─────────┐
    ▼                   ▼
ImageBBoxAnnotator   ComponentTree
框上显示 "input"     节点显示 "input"
```

---

## 四、数据流

### 4.1 输入流程

```
原始 JSON 数据
      │
      ▼
┌─────────────────────────────────────┐
│ 数据解析器                          │
│ 1. 根据 image.field 获取图片路径    │
│ 2. 应用 pathClean 清洗路径          │
│ 3. 根据 bboxSource 配置提取 bbox    │
│ 4. 组装 bbox + 属性数据             │
│ 5. 生成内部 ID                      │
└─────────────────────────────────────┘
      │
      ▼
bboxList: BboxItem[]
```

### 4.2 输出流程

```
bboxList（内存中的标注结果）
      │
      ▼
┌─────────────────────────────────────┐
│ 数据导出器                          │
│ 1. 根据 output.fields 选择字段      │
│ 2. 根据 path 映射回原数据结构       │
│ 3. 保持原始 JSON 结构               │
└─────────────────────────────────────┘
      │
      ▼
导出数据（与原数据结构一致）
```

---

## 五、组件内部结构

```
ImageBBoxAnnotator
│
├── header（标题栏）
│   - title（自定义标题）
│   - 操作按钮：显示全部、放大模式、重置
│
├── ImageCanvas（图片画布）
│   - 图片显示
│   - bbox 框绘制
│   - 框上显示 representField 的值
│   - 拖拽调整 bbox
│   - 点击选中
│   - 右键新建 bbox
│
└── BboxPropertyEditor（属性编辑器）
    - 遍历 bboxProperties 渲染表单
    - bbox 坐标编辑（x1, y1, x2, y2）
    - 动态属性编辑
    - 新建 bbox 按钮
    - 删除 bbox 按钮
```

---

## 六、配置面板设计

```
┌─────────────────────────────────────────────────────────────┐
│  组件配置：ImageBBoxAnnotator                                │
│  标题：[图片标注器        ]                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ▼ 图片设置                                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 图片字段：[image            ▼]                          ││
│  │ [x] 启用路径清洗                                         ││
│  │ 清除前缀：[/mnt/data/      ]                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ▼ BBox 数据源                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 模式：○ 列表格式  ○ 对话提取                            ││
│  │                                                         ││
│  │ [列表格式]                                               ││
│  │   数据路径：[items           ▼]                         ││
│  │   bbox字段：[bbox            ▼]                         ││
│  │                                                         ││
│  │ [对话提取]                                               ││
│  │   对话字段：[conversations    ▼]                        ││
│  │   提取正则：[\[(\d+,\s*\d+,...)\]]                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ▼ BBox 属性定义                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ┌─────┬──────────┬──────────┬──────────────┐           ││
│  │ │ 属性│ 来源字段  │ 显示名称 │ 默认值       │           ││
│  │ ├─────┼──────────┼──────────┼──────────────┤           ││
│  │ │ type│ [type  ▼]│ 类型     │ unknown      │           ││
│  │ │text │ [text  ▼]│ 文本内容 │              │           ││
│  │ └─────┴──────────┴──────────┴──────────────┘           ││
│  │                                                         ││
│  │ 代表属性：[type          ▼] ← 框上显示此字段的值        ││
│  │                                                         ││
│  │ [+ 添加属性]  [自动推断字段]                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ▼ 输出设置                                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 输出字段：                                               ││
│  │   [x] bbox    [x] type    [x] text                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 七、示例场景

### 场景 1：列表格式数据

```json
{
  "image": "/mnt/data/images/img001.jpg",
  "annotations": [
    { "bbox": [0, 0, 100, 50], "type": "button", "text": "提交" },
    { "bbox": [100, 0, 200, 50], "type": "input", "text": "" }
  ]
}
```

配置：
```typescript
{
  title: "图片标注器",
  image: { field: "image", pathClean: { enabled: true, prefix: "/mnt/data/" } },
  bboxSource: { mode: "list", dataPath: "annotations", bboxField: "bbox" },
  bboxProperties: [
    { name: "type", sourceField: "type", displayName: "类型", defaultValue: "unknown" },
    { name: "text", sourceField: "text", displayName: "文本", defaultValue: "" }
  ],
  representField: "type",
  output: { fields: ["bbox", "type", "text"] }
}
```

### 场景 2：对话提取模式

```json
{
  "image": "img002.jpg",
  "conversations": [
    { "from": "human", "value": "图中[0,0,100,50]是什么？" },
    { "from": "agent", "value": "是一个按钮" }
  ]
}
```

配置：
```typescript
{
  title: "对话标注器",
  image: { field: "image" },
  bboxSource: {
    mode: "conversation",
    conversationPath: "conversations",
    extractRegex: "\\[(\\d+,\\s*\\d+,\\s*\\d+,\\s*\\d+)\\]"
  },
  bboxProperties: [
    { name: "content", sourceField: "conversations[1].value", displayName: "内容", defaultValue: "" }
  ],
  representField: "content",
  output: { fields: ["bbox", "content"] }
}
```