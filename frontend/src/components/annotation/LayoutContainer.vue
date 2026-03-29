<script setup lang="ts">
/**
 * 两列布局容器组件
 * 支持可调整宽度的两列布局
 */
import { ref, computed, watch } from 'vue'
import type { LayoutConfig, ColumnConfig } from '@/types/annotation-tool'
import AnnotationPanel from './AnnotationPanel.vue'

interface Props {
  layout: LayoutConfig
  readonly?: boolean
  leftColumnWidth?: number  // 左列宽度（像素）
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  leftColumnWidth: 350
})

const emit = defineEmits<{
  'update:layout': [layout: LayoutConfig]
  'update:leftColumnWidth': [width: number]  // 左列宽度变化
}>()

// 拖拽调整状态
const isResizing = ref(false)
const resizeColumn = ref<'left' | null>(null)
const resizeStartX = ref(0)
const resizeStartWidth = ref(0)

// 内部列宽状态
const internalLeftWidth = ref(props.leftColumnWidth)

// 监听外部宽度变化
watch(() => props.leftColumnWidth, (newWidth) => {
  internalLeftWidth.value = newWidth
})

// 开始调整列宽
const startResize = (column: 'left', event: MouseEvent) => {
  if (props.readonly) return

  isResizing.value = true
  resizeColumn.value = column
  resizeStartX.value = event.clientX
  resizeStartWidth.value = internalLeftWidth.value

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}

// 处理调整
const handleResize = (event: MouseEvent) => {
  if (!isResizing.value) return

  const deltaX = event.clientX - resizeStartX.value
  const newWidth = Math.max(200, resizeStartWidth.value + deltaX)

  if (resizeColumn.value === 'left') {
    internalLeftWidth.value = newWidth
  }
}

// 停止调整
const stopResize = () => {
  isResizing.value = false
  resizeColumn.value = null
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)

  // 通知父组件宽度变化
  emit('update:leftColumnWidth', internalLeftWidth.value)
}

// 获取列宽样式
const getLeftColumnWidth = computed(() => `${internalLeftWidth.value}px`)

// 暴露方法给父组件获取当前宽度
defineExpose({
  getLeftColumnWidth: () => internalLeftWidth.value
})
</script>

<template>
  <div class="layout-container" :class="{ 'is-resizing': isResizing }">
    <!-- 左列 -->
    <div
      class="column column-left"
      :style="{ width: getLeftColumnWidth }"
    >
      <slot name="left">
        <template v-for="panel in layout.left.panels" :key="panel.id">
          <AnnotationPanel
            :panel="panel"
            :readonly="readonly"
          />
        </template>
      </slot>
    </div>

    <!-- 左列调整手柄 -->
    <div
      v-if="!readonly"
      class="resize-handle resize-handle-left"
      @mousedown="startResize('left', $event)"
    >
      <div class="resize-handle-bar"></div>
    </div>

    <!-- 中列 -->
    <div class="column column-center">
      <slot name="center">
        <template v-for="panel in layout.center.panels" :key="panel.id">
          <AnnotationPanel
            :panel="panel"
            :readonly="readonly"
          />
        </template>
      </slot>
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout-container {
  display: flex;
  height: 100%;
  width: 100%;
  min-width: 0;
  position: relative;
}

.column {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: #FFFFFF;
}

.column-left {
  flex-shrink: 0;
  border-right: 1px solid #E5E7EB;
}

.column-center {
  flex: 1;
  min-width: 0;
}

.resize-handle {
  width: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: col-resize;
  transition: background 0.15s ease;
  position: relative;
  z-index: 10;

  &:hover {
    background: #E8F3FF;
  }
}

.resize-handle-bar {
  width: 4px;
  height: 40px;
  border-radius: 2px;
  background: #E5E7EB;
  transition: background 0.15s ease;

  .resize-handle:hover & {
    background: #165DFF;
  }
}

.is-resizing {
  cursor: col-resize;
  user-select: none;

  .resize-handle-bar {
    background: #165DFF;
  }
}
</style>
