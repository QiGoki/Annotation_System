<script setup lang="ts">
/**
 * 标注面板组件 v4
 *
 * 用于显示工具面板，支持多种组件类型
 */
import { ref, computed } from 'vue'
import type { PanelConfig } from '@/types/annotation-tool'
import ImageBBoxAnnotator from './ImageBBoxAnnotator.vue'
import TextViewer from './TextViewer.vue'
import RadioSelector from './RadioSelector.vue'
import TextInput from './TextInput.vue'

interface Props {
  panel: PanelConfig
  readonly?: boolean
  config?: any  // 模块配置
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  config: {}
})

const emit = defineEmits<{
  'update:panel': [panel: PanelConfig]
  'update:collapsed': [collapsed: boolean]
}>()

// 面板展开状态
const isCollapsed = ref(!props.panel.defaultExpanded)
const isExpanded = computed(() => !isCollapsed.value)

// 切换展开/折叠
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('update:collapsed', isCollapsed.value)
}
</script>

<template>
  <div class="annotation-panel" :class="{ collapsed: isCollapsed }">
    <!-- 面板头部 -->
    <div
      v-if="panel.collapsible !== false"
      class="panel-header"
      @click="toggleCollapse"
    >
      <span class="panel-title">{{ panel.title }}</span>
      <span class="panel-toggle">{{ isCollapsed ? '▶' : '▼' }}</span>
    </div>

    <!-- 面板内容 -->
    <div v-show="isExpanded" class="panel-content">
      <!-- 图片拉框标注器 -->
      <ImageBBoxAnnotator
        v-if="panel.toolId === 'ImageBBoxAnnotator'"
        :title="panel.title"
        :readonly="readonly"
      />

      <!-- 文本查看器 -->
      <TextViewer
        v-else-if="panel.toolId === 'TextViewer'"
        :config="config"
      />

      <!-- 单选组件 -->
      <RadioSelector
        v-else-if="panel.toolId === 'RadioSelector'"
        :config="config"
      />

      <!-- 文本输入 -->
      <TextInput
        v-else-if="panel.toolId === 'TextInput'"
        :config="config"
      />

      <!-- 未知工具 -->
      <div v-else class="unknown-tool">
        未知工具：{{ panel.toolId }}
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.annotation-panel {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #E5E7EB;

  &:last-child {
    border-bottom: none;
  }

  &.collapsed {
    .panel-header {
      border-bottom: none;
    }
  }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #F9FAFB;
  cursor: pointer;
  transition: background 0.15s ease;
  border-bottom: 1px solid #E5E7EB;

  &:hover {
    background: #F3F4F6;
  }
}

.panel-title {
  font-weight: 600;
  font-size: 13px;
  color: #111827;
}

.panel-toggle {
  font-size: 12px;
  color: #9CA3AF;
}

.panel-content {
  flex: 1;
  overflow: auto;
  background: #FFFFFF;
}

.unknown-tool {
  padding: 20px;
  text-align: center;
  color: #9CA3AF;
  font-size: 13px;
}
</style>