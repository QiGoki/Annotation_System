<script setup lang="ts">
/**
 * 标注面板组件
 * 用于显示工具面板或自定义内容
 */
import { ref, computed } from 'vue'
import type { PanelConfig } from '@/types/annotation-tool'
import ImageBBoxAnnotator from './ImageBBoxAnnotator.vue'
import ComponentTree from './ComponentTree.vue'

interface Props {
  panel: PanelConfig
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
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

// 渲染工具组件
const renderToolComponent = () => {
  const toolId = props.panel.toolId

  if (toolId === 'image_bbox') {
    return h(ImageBBoxAnnotator, {
      imageUrl: props.props?.imageUrl || '',
      bboxes: props.props?.bboxes || [],
      selectedBboxPath: props.props?.selectedBboxPath || null,
      showAllBboxes: props.props?.showAllBboxes || false,
      zoomable: props.panel.props?.zoomable ?? true,
      bboxEditable: props.panel.props?.bboxEditable ?? true,
      'onUpdate:selectedBboxPath': (path: number[] | null) => {
        emit('update:panel', {
          ...props.panel,
          props: { ...props.panel.props, selectedBboxPath: path }
        })
      },
      'onUpdate:bbox': (path: number[], bbox: [number, number, number, number]) => {
        const bboxes = (props.props?.bboxes || []).map((b: any) =>
          b.path.join('-') === path.join('-') ? { ...b, bbox } : b
        )
        emit('update:panel', {
          ...props.panel,
          props: { ...props.panel.props, bboxes }
        })
      }
    })
  }

  if (toolId === 'component_tree') {
    return h(ComponentTree, {
      components: props.props?.components || [],
      selectedPath: props.props?.selectedPath || null,
      expandedPaths: props.props?.expandedPaths || {},
      readonly: props.readonly,
      'onUpdate:components': (components: any[]) => {
        emit('update:panel', {
          ...props.panel,
          props: { ...props.panel.props, components }
        })
      },
      'onUpdate:selectedPath': (path: number[] | null) => {
        emit('update:panel', {
          ...props.panel,
          props: { ...props.panel.props, selectedPath: path }
        })
      },
      'onUpdate:expandedPaths': (paths: Record<string, boolean>) => {
        emit('update:panel', {
          ...props.panel,
          props: { ...props.panel.props, expandedPaths: paths }
        })
      }
    })
  }

  // 未知工具类型
  return h('div', { class: 'unknown-tool' }, `未知工具：${toolId}`)
}

// 手动导入 h 函数
import { h } from 'vue'
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
      <!-- 工具组件 -->
      <component
        :is="renderToolComponent()"
        v-if="panel.type === 'tool' && panel.toolId"
      />

      <!-- 自定义内容插槽 -->
      <slot v-else name="custom"></slot>
    </div>
  </div>
</template>

<style scoped lang="scss">
.annotation-panel {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid var(--bili-border, #e3e5e7);

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
  padding: 10px 15px;
  background: var(--bili-bg, #f4f5f7);
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--bili-border, #e3e5e7);

  &:hover {
    background: var(--bili-border, #e3e5e7);
  }
}

.panel-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--bili-text-primary, #212121);
}

.panel-toggle {
  font-size: 12px;
  color: var(--bili-text-secondary, #9499a0);
}

.panel-content {
  flex: 1;
  overflow: auto;
  background: var(--bili-card-bg, #ffffff);
}

.unknown-tool {
  padding: 20px;
  text-align: center;
  color: var(--bili-text-secondary, #9499a0);
  font-size: 13px;
}
</style>
