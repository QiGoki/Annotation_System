<template>
  <div class="project-config-editor">
    <!-- 信息提示 -->
    <div class="info-alert">
      <div class="alert-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
      </div>
      <div class="alert-content">
        <div class="alert-title">标注配置</div>
        <div class="alert-desc">请在项目创建页面配置标注组件，此处仅显示 JSON 预览。</div>
      </div>
    </div>

    <!-- JSON 预览 -->
    <div class="config-preview">
      <pre class="config-text">{{ displayValue }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectConfig } from '@/types/project'

const props = defineProps<{
  modelValue: ProjectConfig
}>()

const displayValue = computed(() => {
  try {
    return JSON.stringify(props.modelValue, null, 2)
  } catch {
    return ''
  }
})
</script>

<style scoped>
.project-config-editor {
  width: 100%;
}

.info-alert {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #DBEAFE;
  border-radius: 8px;
  margin-bottom: 16px;
}

.alert-icon {
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.alert-desc {
  font-size: 13px;
  color: #6B7280;
  margin-top: 4px;
}

.config-preview {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 12px;
}

.config-text {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #111827;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  line-height: 1.6;
}
</style>