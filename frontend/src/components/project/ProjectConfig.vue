<template>
  <div class="project-config-editor">
    <el-alert
      title="标注配置"
      description="请在项目创建页面配置标注组件，此处仅显示 JSON 预览。"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    />
    <el-input
      :model-value="modelValue"
      type="textarea"
      :rows="10"
      disabled
    />
  </div>
</template>

<script setup lang="ts">
import type { ProjectConfig } from '@/types/project'

defineProps<{
  modelValue: ProjectConfig
}>()
</script>

<style scoped>
.project-config-editor {
  width: 100%;
}
</style>
