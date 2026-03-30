<script setup lang="ts">
/**
 * 标注执行页面 v5
 *
 * 适配新数据结构：Project -> Task -> DataItems
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AnnotationSidebar from '@/components/annotation/AnnotationSidebar.vue'
import LayoutContainer from '@/components/annotation/LayoutContainer.vue'
import ImageBBoxAnnotator from '@/components/annotation/ImageBBoxAnnotator.vue'
import TextViewer from '@/components/annotation/TextViewer.vue'
import RadioSelector from '@/components/annotation/RadioSelector.vue'
import TextInput from '@/components/annotation/TextInput.vue'
import { useAnnotationSidebar } from '@/composables/useAnnotationSidebar'
import { createAnnotationContext } from '@/composables/useAnnotationContext'
import { getModuleById } from '@/composables/useAnnotationModuleRegistry'
import { getTaskDetail, saveAnnotation, submitAnnotation } from '@/api/task'
import { getAnnotationPageConfig, saveAnnotationPageConfig, getProjectDetail } from '@/api/project'
import type { LayoutConfig, PanelConfig, ColumnConfig } from '@/types/annotation-module'

const route = useRoute()
const router = useRouter()

const isPreviewModeFlag = ref(route.path.includes('/preview'))

const taskId = computed(() => Number(route.params.id))
const projectId = computed(() => {
  if (isPreviewModeFlag.value) {
    return Number(route.params.id)
  }
  return task.value?.project_id || 0
})

// 任务数据
const task = ref<any>(null)
const dataItems = ref<any[]>([])
const projectConfig = ref<any>(null)

const loading = ref(false)
const isSaving = ref(false)

const sidebarCollapsed = ref(false)

// 创建 AnnotationContext
const annotationContext = createAnnotationContext()

// 当前选中的数据条目索引
const currentIndex = ref(0)

// 使用新版 LayoutConfig
const layout = ref<LayoutConfig | null>(null)

// 列宽缓存
const columnWidthsCache = ref<number[]>([])

// 布局容器引用
const layoutContainerRef = ref<InstanceType<typeof LayoutContainer> | null>(null)

// 计算当前数据条目
const currentItem = computed(() => dataItems.value[currentIndex.value])

// 统计信息
const stats = computed(() => {
  const total = dataItems.value.length
  const completed = dataItems.value.filter(item => item.status === 'completed').length
  return { total, completed }
})

// 根据状态获取数据条目列表
const completedItems = computed(() => {
  return dataItems.value
    .map((item, index) => ({ ...item, index }))
    .filter(item => item.status === 'completed')
})

const remainingItems = computed(() => {
  return dataItems.value
    .map((item, index) => ({ ...item, index }))
    .filter(item => item.status !== 'completed')
})

// 选择数据条目
const selectItem = (index: number) => {
  currentIndex.value = index
}

// 标记为已保存
const markAsSaved = (index: number) => {
  if (dataItems.value[index]) {
    dataItems.value[index].status = 'doing'
  }
}

// 重置
const reset = () => {
  currentIndex.value = 0
}

// 根据 module.type 返回对应的组件
const getComponentForModule = (moduleType: string) => {
  switch (moduleType) {
    case 'ImageBBoxAnnotator':
      return ImageBBoxAnnotator
    case 'TextViewer':
      return TextViewer
    case 'RadioSelector':
      return RadioSelector
    case 'TextInput':
      return TextInput
    default:
      return null
  }
}

// 构建新版布局配置
const buildLayoutFromConfig = (modules: any[], layoutConfig?: LayoutConfig) => {
  let columns: ColumnConfig[] = []

  if (layoutConfig?.columns && layoutConfig.columns.length > 0) {
    columns = layoutConfig.columns
      .filter(col => col.index > 0)
      .map(col => ({
        ...col,
        panels: []
      }))
  }

  if (columns.length === 0) {
    columns = [
      { index: 1, width: '40%', label: '左列', fill: false, panels: [] },
      { index: 2, width: '60%', label: '右列', fill: false, panels: [] }
    ]
  }

  const panelsByColumn: Record<number, PanelConfig[]> = {}
  columns.forEach(col => {
    panelsByColumn[col.index] = []
  })

  modules.forEach((module) => {
    const moduleDef = getModuleById(module.type)
    const panel: PanelConfig = {
      id: module.id,
      type: 'tool',
      toolId: module.type,
      title: module.config?.title || moduleDef?.name || '未知组件',
      collapsible: true,
      defaultExpanded: true,
      config: module.config
    }

    const targetCol = module.col || 2
    if (panelsByColumn[targetCol]) {
      panelsByColumn[targetCol].push(panel)
    } else {
      const lastColIndex = columns[columns.length - 1]?.index || 2
      if (panelsByColumn[lastColIndex]) {
        panelsByColumn[lastColIndex].push(panel)
      }
    }
  })

  layout.value = {
    columnCount: columns.length,
    columns: columns.map(col => ({
      ...col,
      panels: panelsByColumn[col.index] || []
    }))
  }
}

// 加载任务
const loadTask = async () => {
  loading.value = true
  try {
    // 获取项目信息（包括 image_base_path）
    let imageBasePath: string | null = null
    try {
      const projectDetail = await getProjectDetail(projectId.value)
      imageBasePath = projectDetail.image_base_path || null
    } catch (e) {
      console.warn('[AnnotationRunner] 获取项目详情失败', e)
    }

    // 设置项目信息到 context
    annotationContext.setProjectInfo(projectId.value, imageBasePath)

    if (isPreviewModeFlag.value) {
      // 预览模式
      const configStr = localStorage.getItem('annotation-preview-config')
      const dataStr = localStorage.getItem('annotation-preview-data')

      if (!configStr || !dataStr) {
        alert('预览数据丢失，请重新配置')
        router.push(`/projects/${projectId.value}/configure`)
        return
      }

      const previewConfig = JSON.parse(configStr)
      const previewData = JSON.parse(dataStr)

      // 预览模式：模拟一个任务包含多条数据
      task.value = {
        id: 0,
        project_id: projectId.value,
        name: '预览任务'
      }
      dataItems.value = Array.isArray(previewData) ? previewData.map((item: any, index: number) => ({
        id: index,
        item_index: index,
        data_source: item,
        status: 'pending'
      })) : [{
        id: 0,
        item_index: 0,
        data_source: previewData,
        status: 'pending'
      }]

      projectConfig.value = previewConfig
      if (previewConfig?.modules) {
        buildLayoutFromConfig(previewConfig.modules, previewConfig.layout)
      }

      reset()
      loadCurrentItem()
    } else {
      // 任务模式
      const result = await getTaskDetail(taskId.value)
      task.value = result
      dataItems.value = result.data_items || []
      projectConfig.value = result.project_config

      if (projectConfig.value?.modules) {
        buildLayoutFromConfig(projectConfig.value.modules, projectConfig.value.layout)
      }

      reset()

      // 找到第一个未完成的条目
      const firstUnsavedIndex = dataItems.value.findIndex(item => item.status !== 'completed')
      if (firstUnsavedIndex >= 0) {
        currentIndex.value = firstUnsavedIndex
      }

      loadCurrentItem()
    }
  } catch (e) {
    console.error(e)
    alert(isPreviewModeFlag.value ? '加载预览失败' : '加载任务失败')
  } finally {
    loading.value = false
  }
}

// 加载当前条目
const loadCurrentItem = () => {
  const item = currentItem.value
  if (!item) return

  annotationContext.setRawData(item.data_source)

  if (projectConfig.value?.modules) {
    const imageModule = projectConfig.value.modules.find((m: any) => m.type === 'ImageBBoxAnnotator')
    if (imageModule?.config) {
      annotationContext.setConfig(imageModule.config)
    }
  }
}

// 保存标注
const handleSave = async () => {
  if (isSaving.value) return
  const item = currentItem.value
  if (!item) return

  isSaving.value = true

  try {
    const outputData = annotationContext.getOutputData()

    await saveAnnotation(item.id, {
      result_json: {
        ...item.data_source,
        annotations: outputData,
        _index: currentIndex.value
      }
    })

    markAsSaved(currentIndex.value)
    alert('保存成功')
  } catch (e) {
    alert('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 提交标注
const handleSubmit = async () => {
  if (isSaving.value) return
  const item = currentItem.value
  if (!item) return

  isSaving.value = true

  try {
    const outputData = annotationContext.getOutputData()

    const result = await submitAnnotation(item.id, {
      result_json: {
        ...item.data_source,
        annotations: outputData,
        _index: currentIndex.value
      }
    })

    // 更新状态
    dataItems.value[currentIndex.value].status = 'completed'

    // 跳转到下一条
    if (result.data?.next_item_id) {
      currentIndex.value = result.data.next_item_index
    } else if (currentIndex.value < dataItems.value.length - 1) {
      currentIndex.value++
    }

    alert('提交成功')
  } catch (e) {
    alert('提交失败')
  } finally {
    isSaving.value = false
  }
}

// 列宽变化处理
const handleColumnWidthsChange = (widths: number[]) => {
  columnWidthsCache.value = widths
}

// 保存布局（仅预览模式）
const isSavingLayout = ref(false)
const handleSaveLayout = async () => {
  if (isSavingLayout.value) return
  isSavingLayout.value = true

  try {
    // 获取当前配置
    const configStr = localStorage.getItem('annotation-preview-config')
    if (!configStr) {
      alert('无法获取预览配置')
      return
    }

    const previewConfig = JSON.parse(configStr)

    // 从 LayoutContainer 获取当前列宽（像素）
    let currentWidths: number[] = []
    if (layoutContainerRef.value) {
      currentWidths = layoutContainerRef.value.getColumnWidths()
    }

    // 更新列宽配置（将像素转换为百分比）
    if (currentWidths.length > 0) {
      const totalWidth = currentWidths.reduce((a, b) => a + b, 0)
      if (totalWidth > 0) {
        previewConfig.layout = {
          ...previewConfig.layout,
          columns: previewConfig.layout.columns.map((col: any, index: number) => {
            const pixelWidth = currentWidths[index] || 300
            const percentWidth = Math.round(pixelWidth / totalWidth * 100)
            return {
              ...col,
              width: `${percentWidth}%`,
              panels: undefined
            }
          })
        }
      }
    }

    // 保存到后端
    await saveAnnotationPageConfig(projectId.value, previewConfig)
    alert('布局已保存')

    // 更新 localStorage
    localStorage.setItem('annotation-preview-config', JSON.stringify(previewConfig))
  } catch (e: any) {
    console.error(e)
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    isSavingLayout.value = false
  }
}

// 快捷键
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
    return
  }

  if (e.ctrlKey && e.key === 's') {
    e.preventDefault()
    handleSave()
  }
}

// 监听索引变化，重新加载数据
watch(currentIndex, () => {
  loadCurrentItem()
})

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
      />

      <!-- 主内容区域 -->
      <div class="annotation-content">
        <LayoutContainer
          v-if="layout"
          ref="layoutContainerRef"
          :layout="layout"
          :readonly="false"
          @update:column-widths="handleColumnWidthsChange"
        >
          <!-- 动态渲染每列 -->
          <template v-for="column in layout.columns" :key="column.index" #[`column-${column.index}`]>
            <div class="column-content" :class="{ fill: column.fill }">
              <template v-for="panel in column.panels" :key="panel.id">
                <div class="panel-wrapper" :class="{ fill: column.fill }">
                  <div class="panel-header">
                    <span class="panel-title">{{ panel.title }}</span>
                  </div>
                  <div class="panel-body">
                    <!-- 图片拉框标注器 -->
                    <ImageBBoxAnnotator
                      v-if="panel.toolId === 'ImageBBoxAnnotator'"
                      :title="panel.title"
                      :show-title="false"
                    />
                    <!-- 文本查看器 -->
                    <TextViewer
                      v-else-if="panel.toolId === 'TextViewer'"
                      :config="panel.config"
                      :show-title="false"
                    />
                    <!-- 单选组件 -->
                    <RadioSelector
                      v-else-if="panel.toolId === 'RadioSelector'"
                      :config="panel.config"
                      :show-title="false"
                    />
                    <!-- 文本输入 -->
                    <TextInput
                      v-else-if="panel.toolId === 'TextInput'"
                      :config="panel.config"
                      :show-title="false"
                    />
                    <!-- 未知组件 -->
                    <div v-else class="unknown-module">
                      未知组件：{{ panel.toolId }}
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </template>
        </LayoutContainer>

        <!-- 无布局时的提示 -->
        <div v-else class="no-layout">
          <p>加载布局中...</p>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="annotation-footer">
      <!-- 预览模式：保存布局按钮 -->
      <template v-if="isPreviewModeFlag">
        <button class="btn-footer btn-save-layout" @click="handleSaveLayout" :disabled="isSavingLayout">
          {{ isSavingLayout ? '保存中...' : '保存布局' }}
        </button>
      </template>
      <!-- 任务模式：导航和保存按钮 -->
      <template v-else>
        <button class="btn-footer btn-prev" @click="currentIndex > 0 && currentIndex--" :disabled="currentIndex <= 0">
          ← 上一条
        </button>
        <button class="btn-footer btn-save" @click="handleSave" :disabled="isSaving || !currentItem">
          ✓ 保存
        </button>
        <button class="btn-footer btn-next" @click="currentIndex < dataItems.length - 1 && currentIndex++" :disabled="currentIndex >= dataItems.length - 1">
          下一条 →
        </button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.annotation-runner {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #F9FAFB;
}

.main-container {
  display: flex;
  flex: 1;
  min-height: 0;
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.annotation-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
}

/* 列内容区 */
.column-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: #F9FAFB;
}

/* 平铺模式：列内容区 */
.column-content.fill {
  background: #FFFFFF;
}

.panel-wrapper {
  display: flex;
  flex-direction: column;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  background: #FFFFFF;
  overflow: hidden;
  user-select: none;
  flex-shrink: 0;
}

/* 平铺模式：组件填满高度 */
.panel-wrapper.fill {
  flex: 1;
  flex-shrink: 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
  flex-shrink: 0;
  user-select: none;
}

.panel-title {
  font-weight: 600;
  font-size: 13px;
  color: #111827;
  user-select: none;
}

.panel-body {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* 平铺模式：panel-body 填满剩余空间 */
.panel-wrapper.fill .panel-body {
  flex: 1;
  min-height: 0;
}

.unknown-module {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9CA3AF;
  user-select: none;
}

.no-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6B7280;
}

.annotation-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 16px;
  background: #FFFFFF;
  border-top: 1px solid #E5E7EB;
}

.btn-footer {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn-prev,
.btn-next {
  background: #165DFF;
  color: white;
}

.btn-prev:hover:not(:disabled),
.btn-next:hover:not(:disabled) {
  background: #0E42D2;
}

.btn-save {
  background: #10B981;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: #059669;
}

.btn-save-layout {
  background: #8B5CF6;
  color: white;
}

.btn-save-layout:hover:not(:disabled) {
  background: #7C3AED;
}

.btn-footer:disabled {
  background: #E5E7EB;
  color: #9CA3AF;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 768px) {
  .main-container {
    padding: 8px;
    gap: 8px;
  }

  .annotation-footer {
    padding: 8px;
    gap: 8px;
  }

  .btn-footer {
    padding: 8px 16px;
    font-size: 13px;
  }
}
</style>