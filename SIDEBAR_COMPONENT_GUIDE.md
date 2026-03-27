# AnnotationSidebar 侧边栏组件使用指南

## 概述

`AnnotationSidebar` 是一个可复用的标注侧边栏组件，可以在任何标注页面中使用。它提供了条目列表、统计信息等功能。

**注意**：此组件假设并发控制已在任务领取阶段处理，这里只负责显示当前任务的标注进度。

## 组件结构

```
frontend/src/
├── components/annotation/
│   └── AnnotationSidebar.vue      # 侧边栏组件
├── types/
│   └── annotation-sidebar.ts       # 类型定义
└── composables/
    └── useAnnotationSidebar.ts     # 状态管理 Composable
```

## 快速开始

### 1. 基础用法

```vue
<template>
  <div class="annotation-page">
    <AnnotationSidebar
      :current-index="currentIndex"
      :stats="stats"
      :completed-items="completedItems"
      :remaining-items="remainingItems"
      :title="taskName"
      @select:item="handleItemSelect"
    />

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 标注内容 -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AnnotationSidebar from '@/components/annotation/AnnotationSidebar.vue'
import { useAnnotationSidebar } from '@/composables/useAnnotationSidebar'

// 任务数据（从 API 加载）
const taskName = ref('UI 组件标注')
const taskData = ref<any[]>([...])

// 使用 Composable 管理状态
const {
  currentIndex,
  stats,
  completedItems,
  remainingItems,
  selectItem,
  markAsSaved,
} = useAnnotationSidebar(taskData.value)

// 处理条目选择
const handleItemSelect = (index: number) => {
  selectItem(index)
  // 加载具体条目数据
}
</script>
```

### 2. Props 说明

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `currentIndex` | `number` | `0` | 当前选中的条目索引 |
| `stats` | `SidebarStats` | 计算得出 | 统计数据（自动计算） |
| `completedItems` | `ListItem[]` | 计算得出 | 已完成条目列表（自动计算） |
| `remainingItems` | `ListItem[]` | 计算得出 | 未完成条目列表（自动计算） |
| `collapsed` | `boolean` | `false` | 是否折叠侧边栏 |
| `title` | `string` | `'标注任务'` | 侧边栏标题（动态显示任务名称） |

### 3. Events 说明

| Event | 参数 | 说明 |
|-------|------|------|
| `select:item` | `index: number` | 用户选择条目时触发 |
| `update:collapsed` | `collapsed: boolean` | 侧边栏折叠状态变化时触发 |

## 使用 Composable

`useAnnotationSidebar` Composable 接收任务数据数组，返回状态和方法：

```typescript
import { useAnnotationSidebar } from '@/composables/useAnnotationSidebar'

const {
  // 状态
  currentIndex,        // 当前选中的条目索引
  stats,               // 统计数据（自动计算）
  completedItems,      // 已完成列表（自动计算）
  remainingItems,      // 未完成列表（自动计算）
  savedIndices,        // 已保存的索引集合

  // 方法
  selectItem,          // 选择条目
  markAsSaved,         // 标记为已保存
  isSaved,             // 检查是否已保存
  reset,               // 重置状态（切换任务时使用）
} = useAnnotationSidebar(taskData.value)
```

## 完整示例

```vue
<template>
  <div class="annotation-page">
    <AnnotationSidebar
      :current-index="currentIndex"
      :stats="stats"
      :completed-items="completedItems"
      :remaining-items="remainingItems"
      :title="currentTask.name"
      @select:item="handleItemSelect"
    />

    <div class="main-content">
      <div v-if="currentItem" class="annotation-tools">
        <!-- 你的标注工具 -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AnnotationSidebar from '@/components/annotation/AnnotationSidebar.vue'
import { useAnnotationSidebar } from '@/composables/useAnnotationSidebar'
import { getTaskDetail } from '@/api/task'

const route = useRoute()
const taskId = ref(Number(route.params.id))

// 任务数据
const currentTask = ref({ id: 0, name: '标注任务' })
const taskData = ref<any[]>([])

// 使用 Composable
const {
  currentIndex,
  stats,
  completedItems,
  remainingItems,
  selectItem,
  markAsSaved,
  isSaved,
} = useAnnotationSidebar(taskData.value)

// 当前条目
const currentItem = computed(() => taskData.value[currentIndex.value])

// 加载任务
const loadTask = async () => {
  const res = await getTaskDetail(taskId.value)
  currentTask.value = res
  taskData.value = res.data || []
}

// 处理条目选择
const handleItemSelect = (index: number) => {
  selectItem(index)
}

// 保存标注
const handleSave = async () => {
  // TODO: 调用保存 API
  await saveAnnotation(taskId.value, currentItem.value)
  markAsSaved(currentIndex.value)
}

// 快捷键
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
    return
  }

  // Ctrl+S 保存
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault()
    handleSave()
  }

  // 方向键导航
  if (e.key === 'ArrowRight' && currentIndex.value < taskData.value.length - 1) {
    handleItemSelect(currentIndex.value + 1)
  } else if (e.key === 'ArrowLeft' && currentIndex.value > 0) {
    handleItemSelect(currentIndex.value - 1)
  }
}

onMounted(() => {
  loadTask()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>
```

## 样式定制

组件使用 CSS 变量定义主题色：

```scss
:root {
  --bili-pink: #fb7299;
  --bili-pink-hover: #ff85a7;
  --bili-bg: #f4f5f7;
  --bili-card-bg: #ffffff;
  --bili-text-primary: #212121;
  --bili-text-secondary: #9499a0;
  --bili-border: #e3e5e7;
}
```

## 功能特点

1. **进度统计** - 自动计算总数、已完成、未完成
2. **条目列表** - 已完成/未完成分类显示
3. **快速导航** - 点击列表项快速跳转
4. **折叠功能** - 侧边栏可折叠，节省空间
5. **任务名称** - 动态显示当前任务名称
