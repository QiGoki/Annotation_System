<script setup lang="ts">
/**
 * RadioSelector - 单选/多选组件
 */
import { ref, computed, watch } from 'vue'
import { useAnnotationContext } from '@/composables/useAnnotationContext'

const props = defineProps<{
  config?: {
    title?: string
    field?: string
    options?: string[] | { label: string; value: string }[]
    layout?: 'horizontal' | 'vertical'
    multiSelect?: boolean
  }
  showTitle?: boolean
}>()

const context = useAnnotationContext()
const { rawData, selectedBbox, bboxList } = context

// 是否多选模式
const isMultiSelect = computed(() => props.config?.multiSelect === true)

// 获取字段值
const getFieldValue = (): any => {
  const field = props.config?.field
  if (!field) return ''

  // 优先从选中的 bbox 获取
  if (selectedBbox.value && selectedBbox.value[field] !== undefined) {
    return selectedBbox.value[field]
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
    return current ?? ''
  }

  return ''
}

// 设置字段值
const setFieldValue = (value: any) => {
  const field = props.config?.field
  if (!field) return

  // 优先更新选中的 bbox
  if (selectedBbox.value) {
    context.updateBbox(selectedBbox.value.id, field, value)
    return
  }

  // 否则更新 rawData
  if (rawData.value) {
    const segments = field.match(/[^.[\]]+|\[\d+\]/g) || []
    let current = rawData.value
    for (let i = 0; i < segments.length - 1; i++) {
      const seg = segments[i]
      if (seg.startsWith('[') && seg.endsWith(']')) {
        current = current[parseInt(seg.slice(1, -1))]
      } else {
        current = current[seg]
      }
    }
    const lastSeg = segments[segments.length - 1]
    if (lastSeg.startsWith('[') && lastSeg.endsWith(']')) {
      current[parseInt(lastSeg.slice(1, -1))] = value
    } else {
      current[lastSeg] = value
    }
  }
}

// 当前选中的值（单选）
const selectedValue = ref('')

// 多选模式下的选中值数组
const selectedArray = ref<string[]>([])

// 从数据源同步到本地状态
watch([() => rawData.value, () => selectedBbox.value], () => {
  const val = getFieldValue()
  if (isMultiSelect.value) {
    if (Array.isArray(val)) {
      selectedArray.value = val
    } else if (typeof val === 'string' && val) {
      selectedArray.value = val.split(',').filter(Boolean)
    } else {
      selectedArray.value = []
    }
  } else {
    selectedValue.value = val || ''
  }
}, { immediate: true })

// 标准化选项列表
const options = computed(() => {
  const opts = props.config?.options
  if (!opts || opts.length === 0) {
    return [
      { label: '选项1', value: '选项1' },
      { label: '选项2', value: '选项2' },
      { label: '选项3', value: '选项3' }
    ]
  }
  return opts.map(opt => {
    if (typeof opt === 'string') {
      return { label: opt, value: opt }
    }
    return opt
  })
})

// 检查是否选中
const isChecked = (value: string): boolean => {
  if (isMultiSelect.value) {
    return selectedArray.value.includes(value)
  }
  return selectedValue.value === value
}

// 点击选项
const handleToggle = (value: string) => {
  if (isMultiSelect.value) {
    // 多选模式：切换选中状态
    const current = [...selectedArray.value]
    const index = current.indexOf(value)

    if (index > -1) {
      current.splice(index, 1)
    } else {
      current.push(value)
    }

    selectedArray.value = current
    setFieldValue(current)
  } else {
    // 单选模式
    selectedValue.value = value
    setFieldValue(value)
  }
}

// 配置
const title = computed(() => props.config?.title || '选项')
const layout = computed(() => props.config?.layout || 'vertical')
</script>

<template>
  <div class="radio-selector">
    <!-- 标题 -->
    <div v-if="showTitle !== false" class="selector-header">
      <span class="selector-title">{{ title }}</span>
      <span v-if="isMultiSelect" class="selector-hint">（可多选）</span>
    </div>

    <!-- 选项列表 -->
    <div class="selector-options" :class="layout">
      <div
        v-for="opt in options"
        :key="opt.value"
        class="option-item"
        :class="{ checked: isChecked(opt.value) }"
        @click="handleToggle(opt.value)"
      >
        <!-- 复选框/单选框图标 -->
        <span class="check-box" :class="{ checkbox: isMultiSelect, radio: !isMultiSelect }">
          <span v-if="isChecked(opt.value)" class="check-mark">✓</span>
        </span>
        <!-- 标签 -->
        <span class="option-label">{{ opt.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.radio-selector {
  padding: 12px;
  background: white;
  border-radius: 8px;
  user-select: none;
  min-height: 100px;  /* 最小高度 */
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
  user-select: none;
}

.selector-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  user-select: none;
}

.selector-hint {
  font-size: 12px;
  color: #9CA3AF;
  user-select: none;
}

.selector-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selector-options.horizontal {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 16px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.option-item:hover {
  background: #F3F4F6;
}

.option-item.checked {
  background: #E8F3FF;
}

.check-box {
  width: 18px;
  height: 18px;
  border: 2px solid #D1D5DB;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

.check-box.radio {
  border-radius: 50%;
}

.check-box.checkbox {
  border-radius: 4px;
}

.option-item.checked .check-box {
  border-color: #165DFF;
  background: #165DFF;
}

.check-mark {
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.option-label {
  font-size: 14px;
  color: #374151;
}

.option-item.checked .option-label {
  color: #165DFF;
  font-weight: 500;
}
</style>