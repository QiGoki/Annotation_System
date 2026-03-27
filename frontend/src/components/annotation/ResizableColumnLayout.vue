<script setup lang="ts">
/**
 * 可调整列宽的布局容器
 * 支持鼠标拖拽调整列宽
 */
import { ref, computed } from 'vue'
import { useResizableColumns } from '@/composables/useResizableColumns'

interface Column {
  index: number
  label: string
  width?: string
}

interface Props {
  columns: Column[]
  defaultWidths?: number[]  // 默认宽度百分比
}

const props = withDefaults(defineProps<Props>(), {
  defaultWidths: () => [25, 45, 30]
})

const emit = defineEmits<{
  'update:widths': [widths: number[]]
}>()

const containerRef = ref<HTMLElement | null>(null)

// 使用可调整列宽的 composable
const {
  columnPercents,
  isResizing,
  startResize,
  getColumnStyle
} = useResizableColumns(containerRef, props.defaultWidths)

// 列宽拖拽手柄的 hover 状态
const hoverColumnIndex = ref(-1)

// 处理鼠标进入拖拽手柄
const handleResizerEnter = (index: number) => {
  hoverColumnIndex.value = index
}

// 处理鼠标离开拖拽手柄
const handleResizerLeave = (index: number) => {
  hoverColumnIndex.value = -1
}

// 列是否应该显示
const isColumnVisible = (index: number) => {
  return index < props.columns.length
}
</script>

<template>
  <div class="resizable-columns-container" ref="containerRef">
    <div class="resizable-columns">
      <template v-for="(column, index) in columns" :key="column.index">
        <!-- 列内容 -->
        <div
          class="resizable-column"
          :style="getColumnStyle(index)"
        >
          <slot :name="`column-${column.index}`">
            <div class="column-content">
              <div class="column-header">
                {{ column.label }}
                <span class="column-width">{{ columnPercents[index].toFixed(1) }}%</span>
              </div>
              <div class="column-body">
                <slot :name="`column-body-${column.index}`"></slot>
              </div>
            </div>
          </slot>
        </div>

        <!-- 列之间的拖拽手柄（最后一列不显示） -->
        <div
          v-if="index < columns.length - 1"
          class="column-resizer"
          :class="{
            'resizing': isResizing && hoverColumnIndex === index,
            'hovered': hoverColumnIndex === index
          }"
          @mousedown="(e) => startResize(e, index)"
          @mouseenter="handleResizerEnter(index)"
          @mouseleave="handleResizerLeave(index)"
        >
          <div class="resizer-handle"></div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
.resizable-columns-container {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.resizable-columns {
  display: flex;
  width: 100%;
  height: 100%;
}

.resizable-column {
  display: flex;
  flex-direction: column;
  min-width: 100px;
  overflow: hidden;
  background: #f4f5f7;
  border-right: 1px solid #e3e5e7;

  &:last-child {
    border-right: none;
  }
}

.column-content {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #e9ecef;
  font-size: 13px;
  font-weight: 600;
  color: #666;
  border-bottom: 1px solid #e3e5e7;
  flex-shrink: 0;

  .column-width {
    font-size: 11px;
    color: #999;
    font-weight: normal;
  }
}

.column-body {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

// 拖拽手柄
.column-resizer {
  width: 8px;
  margin-left: -8px;
  position: relative;
  z-index: 10;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &:hover,
  &.hovered {
    background: rgba(251, 114, 153, 0.2);
  }

  &.resizing,
  &:active {
    background: rgba(251, 114, 153, 0.3);
  }
}

.resizer-handle {
  width: 4px;
  height: 24px;
  background: #d0d7de;
  border-radius: 2px;
  transition: all 0.2s;

  .column-resizer:hover &,
  .column-resizer:active & {
    background: #fb7299;
    height: 32px;
  }
}

// 调整时的全局样式
.resizable-columns-container.resizing {
  user-select: none;
  * {
    cursor: col-resize !important;
  }
}
</style>
