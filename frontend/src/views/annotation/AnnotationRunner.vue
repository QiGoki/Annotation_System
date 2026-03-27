<script setup lang="ts">
/**
 * 标注执行页面 - 模块化版本
 * 集成侧边栏、三列布局、标注工具
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AnnotationSidebar from '@/components/annotation/AnnotationSidebar.vue'
import LayoutContainer from '@/components/annotation/LayoutContainer.vue'
import { useAnnotationSidebar } from '@/composables/useAnnotationSidebar'
import { getModuleById } from '@/composables/useAnnotationModuleRegistry'
import { getTaskDetail, saveAnnotation } from '@/api/task'
import { getAnnotationPageConfig } from '@/api/project'
import type { LayoutConfig } from '@/types/annotation-tool'
import type { ComponentNode, BboxData } from '@/types/annotation-tool'
import type { PageConfig, ModuleInstance } from '@/types/annotation-module'

const route = useRoute()
const router = useRouter()

// 检查是否是预览模式（用于条件判断）
const isPreviewModeFlag = ref(route.path.includes('/preview'))

// 根据路由类型获取正确的 ID
// 预览模式：/projects/:id/preview → id 是 projectId
// 标注模式：/annotate/:id → id 是 taskId
const taskId = computed(() => {
  if (isPreviewModeFlag.value) return 0 // 预览模式不需要 taskId
  return Number(route.params.id)
})

const projectId = computed(() => {
  if (isPreviewModeFlag.value) {
    // 预览模式：从路由参数获取 projectId
    return Number(route.params.id)
  }
  // 标注模式：从 task 数据中获取 projectId
  return task.value?.project_id || 0
})

// 任务数据
const task = ref<any>(null)
const taskData = ref<any[]>([])
const loading = ref(false)
const isSaving = ref(false)

// 预览配置（用于预览模式）
const _previewConfig = ref<PageConfig | null>(null)
const _previewData = ref<any>(null)

// 标注状态
const selectedBboxPath = ref<number[] | null>(null)
const selectedComponentPath = ref<number[] | null>(null)
const showAllBboxes = ref(false)
const sidebarCollapsed = ref(false)

// 使用侧边栏 composable
const {
  currentIndex,
  stats,
  completedItems,
  remainingItems,
  selectItem,
  markAsSaved,
  reset
} = useAnnotationSidebar(taskData.value)

// 布局配置 - 将从配置加载
const layout = ref<LayoutConfig>({
  left: { panels: [] },
  center: { panels: [] },
  right: { panels: [] }
})

// 当前组件数据
const currentComponents = ref<ComponentNode[]>([])
const currentBboxes = ref<BboxData[]>([])

// 从模块配置生成布局
const buildLayoutFromConfig = (modules: ModuleInstance[]) => {
  const leftPanels: any[] = []
  const centerPanels: any[] = []

  modules.forEach((module) => {
    const moduleDef = getModuleById(module.type)
    const panel = {
      id: module.id,
      type: 'tool' as const,
      toolId: module.type,
      title: moduleDef?.name || '未知组件',
      collapsible: true,
      defaultExpanded: true,
      props: module.props || {}
    }

    if (module.col === 1) {
      leftPanels.push(panel)
    } else {
      // col === 2 或默认情况都放到中列
      centerPanels.push(panel)
    }
  })

  layout.value = {
    left: { panels: leftPanels },
    center: { panels: centerPanels },
    right: { panels: [] }
  }
}

// 加载任务
const loadTask = async () => {
  loading.value = true
  try {
    // 预览模式：从 sessionStorage 加载
    if (isPreviewModeFlag.value) {
      const configStr = sessionStorage.getItem('annotation-preview-config')
      const dataStr = sessionStorage.getItem('annotation-preview-data')

      if (!configStr || !dataStr) {
        ElMessage.error('预览数据丢失，请重新配置')
        router.push(`/projects/${projectId.value}/configure`)
        return
      }

      _previewConfig.value = JSON.parse(configStr)
      _previewData.value = JSON.parse(dataStr)
      taskData.value = [_previewData.value]

      // 根据配置生成布局
      if (_previewConfig.value?.modules) {
        buildLayoutFromConfig(_previewConfig.value.modules)
      }

      // 更新 composable 中的数据引用
      reset()
      loadCurrentItem()

      ElMessage.info('预览模式：使用示例数据')
    } else {
      // 正常模式：从 API 加载任务和配置
      const result = await getTaskDetail(taskId.value)
      task.value = result
      taskData.value = result.data || []

      // 尝试加载项目配置
      try {
        const pageConfig = await getAnnotationPageConfig(projectId.value)
        if (pageConfig?.modules) {
          buildLayoutFromConfig(pageConfig.modules)
        }
      } catch (e) {
        // 如果没有配置，使用默认布局
        console.warn('未找到页面配置，使用默认布局')
      }

      // 更新 composable 中的数据引用
      reset()

      // 加载第一个未完成的项目
      const firstUnsavedIndex = taskData.value.findIndex((item: any) => !item._saved)
      if (firstUnsavedIndex >= 0) {
        currentIndex.value = firstUnsavedIndex
      }

      loadCurrentItem()
    }
  } catch (e: any) {
    ElMessage.error(isPreviewModeFlag.value ? '加载预览失败' : '加载任务失败')
  } finally {
    loading.value = false
  }
}

// 加载当前条目
const loadCurrentItem = () => {
  const item = taskData.value[currentIndex.value]
  if (!item) return

  // 加载组件数据
  currentComponents.value = item.components || []
  currentBboxes.value = extractBboxes(currentComponents.value)

  // 重置选中状态
  selectedBboxPath.value = null
  selectedComponentPath.value = null
  showAllBboxes.value = false
}

// 从组件树提取 bbox 数据
const extractBboxes = (components: ComponentNode[], path: number[] = []): BboxData[] => {
  const bboxes: BboxData[] = []

  components.forEach((comp, index) => {
    const currentPath = [...path, index]
    if (comp.bbox) {
      bboxes.push({
        path: currentPath,
        bbox: comp.bbox,
        type: comp.type,
        text: comp.text
      })
    }
    if (comp.children && comp.children.length > 0) {
      bboxes.push(...extractBboxes(comp.children, currentPath))
    }
  })

  return bboxes
}

// 保存标注
const handleSave = async () => {
  if (isSaving.value) return
  isSaving.value = true

  try {
    const item = taskData.value[currentIndex.value]
    if (!item) return

    // 保存标注结果
    await saveAnnotation(taskId.value, {
      ...item,
      components: currentComponents.value,
      _index: currentIndex.value
    })

    // 标记为已保存
    markAsSaved(currentIndex.value)
    ElMessage.success('保存成功')
  } catch (e: any) {
    ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 提交任务
const handleSubmit = async () => {
  try {
    await ElMessageBox.confirm('确定要提交此任务吗？提交后将无法继续编辑。', '确认提交', {
      type: 'warning'
    })

    // TODO: 调用提交 API
    ElMessage.success('任务已提交')
    router.push('/tasks')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('提交失败')
    }
  }
}

// 快捷键
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
    return
  }

  // Ctrl+S 保存
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault()
    handleSave()
  }

  // Z 键切换放大模式（如果图片组件支持）
  if (e.key === 'z' && !e.ctrlKey) {
    // TODO: 触发图片组件的放大模式
  }
}

// 生命周期
onMounted(() => {
  loadTask()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div class="annotation-runner">
    <div class="main-container">
      <!-- 侧边栏 -->
      <AnnotationSidebar
        :current-index="currentIndex"
        :stats="stats"
        :completed-items="completedItems"
        :remaining-items="remainingItems"
        :collapsed="sidebarCollapsed"
        :title="task?.name || '标注任务'"
        @select:item="selectItem"
        @update:collapsed="sidebarCollapsed = $event"
        @submit="handleSubmit"
      />

      <!-- 主内容区域 - 两列布局 -->
      <div class="annotation-content">
        <LayoutContainer
          :layout="layout"
          :readonly="false"
        >
          <!-- 左列插槽 -->
          <template #left>
            <!-- 组件树面板会通过 layout 配置自动渲染 -->
          </template>

          <!-- 中列插槽 -->
          <template #center>
            <!-- 图片标注面板会通过 layout 配置自动渲染 -->
          </template>
        </LayoutContainer>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="annotation-footer">
      <button class="btn btn-prev" @click="loadCurrentItem()" :disabled="currentIndex <= 0">
        ← 上一条
      </button>
      <button class="btn btn-save" @click="handleSave" :disabled="isSaving || !taskData[currentIndex]">
        ✓ 保存
      </button>
      <button class="btn btn-next" @click="loadCurrentItem()" :disabled="currentIndex >= taskData.length - 1">
        下一条 →
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.annotation-runner {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bili-bg, #f4f5f7);
}

.main-container {
  display: flex;
  flex: 1;
  min-height: 0;
  padding: 15px;
  gap: 12px;
  overflow: hidden;
}

.annotation-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--bili-card-bg, #ffffff);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.annotation-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 15px;
  background: var(--bili-card-bg, #ffffff);
  border-top: 1px solid var(--bili-border, #e3e5e7);
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &.btn-prev,
  &.btn-next {
    background: var(--bili-blue, #00aeeC);
    color: white;

    &:hover:not(:disabled) {
      background: var(--bili-blue-dark, #0096c7);
    }
  }

  &.btn-save {
    background: var(--bili-pink, #fb7299);
    color: white;

    &:hover:not(:disabled) {
      background: var(--bili-pink-hover, #ff85a7);
    }
  }

  &:disabled {
    background: var(--bili-border, #e3e5e7);
    cursor: not-allowed;
  }
}
</style>
