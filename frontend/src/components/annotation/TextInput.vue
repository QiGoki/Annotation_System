<script setup lang="ts">
/**
 * TextInput - 自定义文本输入组件
 */
import { ref, computed, watch } from 'vue'
import { useAnnotationContext } from '@/composables/useAnnotationContext'

const props = defineProps<{
  config?: {
    title?: string
    mode?: '绑定已有字段' | '新增字段'
    field?: string
    newFieldName?: string
    placeholder?: string
    required?: boolean
    multiline?: boolean
    maxLength?: number
  }
  showTitle?: boolean
}>()

const context = useAnnotationContext()
const { rawData, selectedBbox } = context

// 内部值
const inputValue = ref('')

// 模式判断
const isBindMode = computed(() => props.config?.mode === '绑定已有字段' || !props.config?.mode)

// 有效字段名
const effectiveField = computed(() => {
  if (isBindMode.value) {
    return props.config?.field || ''
  }
  return props.config?.newFieldName || ''
})

// 获取字段值
const getFieldValue = (): string => {
  const field = effectiveField.value
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
  const field = effectiveField.value
  if (!field) return

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

// 输入处理
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  let value = target.value

  // 限制最大长度
  if (maxLength.value > 0 && value.length > maxLength.value) {
    value = value.slice(0, maxLength.value)
  }

  inputValue.value = value
  setFieldValue(value)
}

// 配置
const title = computed(() => props.config?.title || '文本输入')
const placeholder = computed(() => props.config?.placeholder || '')
const required = computed(() => props.config?.required ?? false)
const multiline = computed(() => props.config?.multiline ?? false)
const maxLength = computed(() => props.config?.maxLength ?? 0)
const shouldShowTitle = computed(() => props.showTitle ?? true)

// 字符计数
const charCount = computed(() => inputValue.value.length)
const showCharCount = computed(() => maxLength.value > 0)
const isEmpty = computed(() => !inputValue.value.trim())
</script>

<template>
  <div class="text-input">
    <div v-if="shouldShowTitle" class="input-header">
      <span class="input-title">
        {{ title }}
        <span v-if="required" class="required-mark">*</span>
      </span>
      <span v-if="showCharCount" class="char-count">
        {{ charCount }} / {{ maxLength }}
      </span>
    </div>

    <!-- 无标题时显示必填标记和字符计数 -->
    <div v-if="!shouldShowTitle && (required || showCharCount)" class="input-meta-row">
      <span v-if="required" class="required-hint">*必填</span>
      <span v-if="showCharCount" class="char-count">
        {{ charCount }} / {{ maxLength }}
      </span>
    </div>

    <div class="input-content">
      <textarea
        v-if="multiline"
        :value="inputValue"
        class="input-field multiline"
        :placeholder="placeholder"
        :class="{ empty: isEmpty && required }"
        rows="3"
        @input="handleInput"
      />
      <input
        v-else
        :value="inputValue"
        class="input-field"
        type="text"
        :placeholder="placeholder"
        :class="{ empty: isEmpty && required }"
        @input="handleInput"
      />
    </div>
  </div>
</template>

<style scoped>
.text-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  user-select: none;
  min-height: 80px;  /* 最小高度 */
}

.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;  /* 禁止标题区域文本选择 */
}

.input-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  user-select: none;
}

.required-mark {
  color: #EF4444;
  font-weight: 500;
  user-select: none;
}

.char-count {
  font-size: 12px;
  color: #9CA3AF;
  user-select: none;
}

.input-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}

.required-hint {
  font-size: 12px;
  color: #EF4444;
  user-select: none;
}

.input-content {
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
  user-select: text;  /* 输入框允许文本选择 */
}

.input-field:focus {
  border-color: #165DFF;
}

.input-field.empty {
  border-color: #FEE2E2;
  background: #FEF2F2;
}

.input-field.multiline {
  resize: vertical;
  min-height: 60px;
}
</style>