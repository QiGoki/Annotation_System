<script setup lang="ts">
/**
 * 标注侧边栏组件
 * 显示任务列表、统计信息、进度等
 */
import { computed } from 'vue'

export interface ListItem {
  index: number
  filename?: string
  saved?: boolean
}

export interface SidebarStats {
  total: number
  completed: number
  remaining: number
}

interface Props {
  currentIndex: number
  stats: SidebarStats
  completedItems: ListItem[]
  remainingItems: ListItem[]
  collapsed?: boolean
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  title: '标注任务'
})

const emit = defineEmits<{
  'select:item': [index: number]
  'update:collapsed': [collapsed: boolean]
  'submit': []
}>()

// 切换折叠状态
const toggleCollapse = () => {
  emit('update:collapsed', !props.collapsed)
}

// 选择条目
const selectItem = (index: number) => {
  emit('select:item', index)
}

// 提交任务
const handleSubmit = () => {
  emit('submit')
}
</script>

<template>
  <div class="annotation-sidebar" :class="{ collapsed }">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <h1>
        <span>🏷️</span>
        {{ title }}
        <button class="sidebar-toggle" @click="toggleCollapse" title="折叠/展开">
          {{ collapsed ? '▶' : '◀' }}
        </button>
      </h1>
    </div>

    <!-- 统计信息 -->
    <div class="file-stats">
      <div class="stat">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总数</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color: #10B981">{{ stats.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ stats.remaining }}</div>
        <div class="stat-label">未完成</div>
      </div>
    </div>

    <!-- 条目列表 -->
    <div class="item-lists" v-if="!collapsed">
      <!-- 已完成列表 -->
      <div class="list-section">
        <div class="list-header">
          <span>✓ 已完成</span>
          <span class="count">{{ completedItems.length }}</span>
        </div>
        <div class="list-items">
          <div
            v-for="item in completedItems"
            :key="item.index"
            :class="['list-item', 'saved', { active: item.index === currentIndex }]"
            @click="selectItem(item.index)"
          >
            <span class="index">{{ item.index + 1 }}</span>
            <span class="filename" :title="item.filename || 'unnamed'">
              {{ item.filename || 'unnamed' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 未完成列表 -->
      <div class="list-section">
        <div class="list-header">
          <span>○ 未完成</span>
          <span class="count">{{ remainingItems.length }}</span>
        </div>
        <div class="list-items">
          <div
            v-for="item in remainingItems"
            :key="item.index"
            :class="['list-item', { active: item.index === currentIndex }]"
            @click="selectItem(item.index)"
          >
            <span class="index">{{ item.index + 1 }}</span>
            <span class="filename" :title="item.filename || 'unnamed'">
              {{ item.filename || 'unnamed' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 侧边栏底部 -->
    <div class="sidebar-footer" v-if="!collapsed">
      <button class="submit-btn" @click="handleSubmit">✓ 提交文件</button>
    </div>

    <!-- 展开按钮（外部） -->
    <button
      v-if="collapsed"
      class="sidebar-toggle-expand"
      @click="toggleCollapse"
      title="展开侧边栏"
    >
      ▶
    </button>
  </div>
</template>

<style scoped lang="scss">
.annotation-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  position: relative;
  transition: width 0.2s ease;

  &.collapsed {
    width: 0;

    .sidebar-header,
    .file-stats,
    .item-lists,
    .sidebar-footer {
      display: none;
    }
  }
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  justify-content: space-between;
  align-items: center;

  h1 {
    color: #165DFF;
    font-size: 16px;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
}

.sidebar-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #9CA3AF;
  font-size: 16px;

  &:hover {
    color: #165DFF;
  }
}

.file-stats {
  padding: 8px 16px;
  background: #F9FAFB;
  font-size: 12px;
  display: flex;
  justify-content: space-around;
}

.stat {
  text-align: center;
}

.stat-value {
  font-weight: 600;
  font-size: 14px;
  color: #111827;
}

.stat-label {
  color: #9CA3AF;
  font-size: 12px;
}

.item-lists {
  flex: 1;
  overflow: auto;
  padding: 8px 0;
}

.list-section {
  border-bottom: 1px solid #E5E7EB;
}

.list-header {
  padding: 8px 16px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #F9FAFB;
  color: #6B7280;

  &:hover {
    background: #F3F4F6;
  }

  .count {
    background: #165DFF;
    color: white;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 12px;
  }
}

.list-items {
  overflow: auto;
}

.list-item {
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: background 0.15s ease;
  color: #6B7280;

  &:hover {
    background: #F9FAFB;
  }

  &.active {
    background: #E8F3FF;
    border-left: 3px solid #165DFF;
  }

  &.saved {
    .index {
      background: #D1FAE5;
      color: #10B981;
    }

    .filename {
      color: #111827;
    }
  }
}

.index {
  background: #F3F4F6;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 12px;
  flex-shrink: 0;
}

.filename {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #E5E7EB;
  background: #F9FAFB;
}

.submit-btn {
  width: 100%;
  padding: 10px 16px;
  background: #165DFF;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #0E42D2;
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    background: #E5E7EB;
    color: #9CA3AF;
    cursor: not-allowed;
    transform: none;
  }
}

.sidebar-toggle-expand {
  position: fixed;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 12px 8px;
  cursor: pointer;
  color: #165DFF;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  font-size: 16px;
  z-index: 100;
  transition: all 0.15s ease;

  &:hover {
    background: #165DFF;
    color: white;
    border-color: #165DFF;
  }
}
</style>
