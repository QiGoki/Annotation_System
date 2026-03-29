<script setup lang="ts">
/**
 * TextViewer - 文本查看/编辑组件
 */
import { ref, computed, watch } from 'vue'
import { useAnnotationContext } from '@/composables/useAnnotationContext'

const props = defineProps<{
  config?: {
    title?: string
    field?: string
    multiline?: boolean
  }
  showTitle?: boolean
}>()

const context = useAnnotationContext()
const { rawData, selectedBbox } = context

// 内部值
const inputValue = ref('')

// 获取字段值
const getFieldValue = (): string => {
  const field = props.config?.field
  if (!field) return ''

  // 优先从选中的 bbox 获取
  if (selectedBbox.value && selectedBbox.value[field] !== undefined) {
    return String(selectedBbox.value[field])
  }

  // 否则从 rawData 获取
  if (rawData.value) {
    const segments = field.match(/[^.[\]]+|\[\d+\]/g) || []
    let current = rawData.value
    for (const seg of segments) {
      if (current === null || current === undefined) return ''
      if (seg.startsWith('[') && seg.endsWith(']')) {
        current = current[parseInt(seg.slice(1, -1))]
      } else {
        current = current[seg]
      }
    }
    return current !== null && current !== undefined ? String(current) : ''
  }

  return ''
}

// 设置字段值
const setFieldValue = (value: string) => {
  const field = props.config?.field
  if (!field) return

  // 更新输入值
  inputValue.value = value

  // 优先更新选中的 bbox
  if (selectedBbox.value) {
    context.updateBbox(selectedBbox.value.id, field, value)
    return
  }

  // 否则更新 rawData
  if (rawData.value) {
    rawData.value[field] = value
  }
}

// 从数据源同步到本地状态
watch([() => rawData.value, () => selectedBbox.value], () => {
  inputValue.value = getFieldValue()
}, { immediate: true })

// 配置
const title = computed(() => props.config?.title || '文本查看')
const multiline = computed(() => props.config?.multiline ?? false)
const shouldShowTitle = computed(() => props.showTitle ?? true)
</script>

<template>
  <div class="text-viewer">
    <div v-if="shouldShowTitle" class="viewer-header">
      <span class="viewer-title">{{ title }}</span>
    </div>

    <div class="viewer-content">
      <!-- 多行输入 -->
      <textarea
        v-if="multiline"
        :value="inputValue"
        class="input-field multiline"
        rows="4"
        placeholder="请输入内容..."
        @input="setFieldValue(($event.target as HTMLTextAreaElement).value)"
      />
      <!-- 单行输入 -->
      <input
        v-else
        :value="inputValue"
        class="input-field"
        type="text"
        placeholder="请输入内容..."
        @input="setFieldValue(($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>

<style scoped>
.text-viewer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  user-select: none;
  min-height: 80px;  /* 最小高度 */
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}

.viewer-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  user-select: none;
}

.viewer-content {
  flex: 1;
}

.input-field {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
  user-select: text;  /* 输入框允许文本选择 */
}

.input-field:focus {
  border-color: #165DFF;
}

.input-field.multiline {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}
</style>