<script setup lang="ts">
/**
 * 标注执行页面 v4 - StepFun风格
 *
 * 使用 AnnotationContext 共享状态，支持多种组件类型
 */
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
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
import { getTaskDetail, saveAnnotation } from '@/api/task'
import { getAnnotationPageConfig, saveAnnotationPageConfig } from '@/api/project'
import type { LayoutConfig, PanelConfig } from '@/types/annotation-tool'
import type { PageConfig, ModuleInstance } from '@/types/annotation-module'

const route = useRoute()
const router = useRouter()

const isPreviewModeFlag = ref(route.path.includes('/preview'))

const taskId = computed(() => {
  if (isPreviewModeFlag.value) return 0
  return Number(route.params.id)
})

const projectId = computed(() => {
  if (isPreviewModeFlag.value) {
    return Number(route.params.id)
  }
  return task.value?.project_id || 0
})

const task = ref<any>(null)
const taskData = ref<any[]>([])
const loading = ref(false)
const isSaving = ref(false)

const _previewConfig = ref<PageConfig | null>(null)
const _previewData = ref<any>(null)
const _pageConfig = ref<PageConfig | null>(null)  // 存储页面配置（用于任务模式）

const sidebarCollapsed = ref(false)

// 创建 AnnotationContext（用于 ImageBBoxAnnotator）
const annotationContext = createAnnotationContext()

const {
  currentIndex,
  stats,
  completedItems,
  remainingItems,
  selectItem,
  markAsSaved,
  reset
} = useAnnotationSidebar(taskData.value)

const layout = ref<LayoutConfig>({
  left: { panels: [] },
  center: { panels: [] },
  right: { panels: [] }
})

// 每列是否平铺满画布（从配置读取）
const fillColumn = ref({
  left: false,
  center: false
})

// 左列宽度
const leftColumnWidth = ref(350)

// 布局容器引用
const layoutContainerRef = ref<InstanceType<typeof LayoutContainer> | null>(null)

// 当前选中的面板 ID
const selectedPanelId = ref<string | null>(null)

// 根据 module.type 返回对应的组件
const getComponentForModule = (moduleType: string) => {
  switch (moduleType) {
    case 'ImageBBoxAnnotator':
      return ImageBBoxAnnotator
    default:
      return null
  }
}

// 构建布局配置
const buildLayoutFromConfig = (modules: ModuleInstance[], layoutConfig?: any) => {
  const leftPanels: PanelConfig[] = []
  const centerPanels: PanelConfig[] = []

  // 读取平铺配置
  if (layoutConfig?.columns) {
    const leftCol = layoutConfig.columns.find((c: any) => c.index === 1)
    const rightCol = layoutConfig.columns.find((c: any) => c.index === 2)
    fillColumn.value.left = leftCol?.fill ?? false
    fillColumn.value.center = rightCol?.fill ?? false
  }

  // 读取左列宽度（预览模式从配置，任务模式从 localStorage）
  if (isPreviewModeFlag.value) {
    leftColumnWidth.value = layoutConfig?.leftColumnWidth || 350
  } else {
    const savedWidth = localStorage.getItem(`annotation-layout-${projectId.value}`)
    if (savedWidth) {
      try {
        const parsed = JSON.parse(savedWidth)
        leftColumnWidth.value = parsed.leftColumnWidth || 350
      } catch (e) {
        leftColumnWidth.value = 350
      }
    }
  }

  // 存储模块配置以便渲染时获取
  const moduleConfigs: Record<string, any> = {}
  modules.forEach(m => {
    moduleConfigs[m.id] = m.config
  })

  modules.forEach((module) => {
    const moduleDef = getModuleById(module.type)
    const panel: PanelConfig = {
      id: module.id,
      type: 'tool',
      toolId: module.type,
      title: module.config?.title || moduleDef?.name || '未知组件',
      collapsible: true,
      defaultExpanded: true
    }

    // 存储配置到 panel（扩展属性）
    ;(panel as any).config = module.config

    if (module.col === 1) {
      leftPanels.push(panel)
    } else {
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
    if (isPreviewModeFlag.value) {
      const configStr = localStorage.getItem('annotation-preview-config')
      const dataStr = localStorage.getItem('annotation-preview-data')

      if (!configStr || !dataStr) {
        alert('预览数据丢失，请重新配置')
        router.push(`/projects/${projectId.value}/configure`)
        return
      }

      _previewConfig.value = JSON.parse(configStr)
      _previewData.value = JSON.parse(dataStr)
      taskData.value = [_previewData.value]

      if (_previewConfig.value?.modules) {
        buildLayoutFromConfig(_previewConfig.value.modules, _previewConfig.value.layout)
      }

      reset()
      loadCurrentItem()
    } else {
      const result = await getTaskDetail(taskId.value)
      task.value = result
      // data_source 是一个数组，包含多条数据
      taskData.value = Array.isArray(result.data_source) ? result.data_source : []

      try {
        const pageConfig = await getAnnotationPageConfig(projectId.value)
        _pageConfig.value = pageConfig
        if (pageConfig?.modules) {
          buildLayoutFromConfig(pageConfig.modules, pageConfig.layout)
        }
      } catch (e) {
        console.warn('未找到页面配置，使用默认布局')
      }

      reset()

      const firstUnsavedIndex = taskData.value.findIndex((item: any) => !item._saved)
      if (firstUnsavedIndex >= 0) {
        currentIndex.value = firstUnsavedIndex
      }

      loadCurrentItem()
    }
  } catch (e) {
    alert(isPreviewModeFlag.value ? '加载预览失败' : '加载任务失败')
  } finally {
    loading.value = false
  }
}

// 加载当前条目
const loadCurrentItem = () => {
  const item = taskData.value[currentIndex.value]
  if (!item) return

  // 设置原始数据到 context
  annotationContext.setRawData(item)

  // 设置 ImageBBoxAnnotator 的配置到 context（用于 bbox 标注）
  const pageConfig = isPreviewModeFlag.value ? _previewConfig.value : _pageConfig.value
  if (pageConfig?.modules) {
    const imageModule = pageConfig.modules.find(m => m.type === 'ImageBBoxAnnotator')
    if (imageModule?.config) {
      annotationContext.setConfig(imageModule.config)
    }
  }

  selectedPanelId.value = null
}

// 保存标注
const handleSave = async () => {
  if (isSaving.value) return
  isSaving.value = true

  try {
    const item = taskData.value[currentIndex.value]
    if (!item) return

    // 获取输出数据
    const outputData = annotationContext.getOutputData()

    await saveAnnotation(taskId.value, {
      result_json: {
        ...item,
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

// 左列宽度变化处理
const handleLeftColumnWidthChange = (width: number) => {
  leftColumnWidth.value = width

  // 任务模式：自动保存到 localStorage
  if (!isPreviewModeFlag.value) {
    localStorage.setItem(`annotation-layout-${projectId.value}`, JSON.stringify({
      leftColumnWidth: width
    }))
  }
}

// 保存布局（仅预览模式）
const isSavingLayout = ref(false)
const handleSaveLayout = async () => {
  if (isSavingLayout.value) return
  isSavingLayout.value = true

  try {
    const pageConfig = _previewConfig.value
    if (!pageConfig) {
      alert('配置不存在')
      return
    }

    // 确保 modules 格式正确
    const modules = pageConfig.modules || []

    const config: PageConfig = {
      modules: modules.map((m: any) => ({
        id: m.id,
        type: m.type,
        col: m.col,
        row: m.row,
        width: m.width,
        height: m.height,
        config: m.config
      })),
      layout: {
        columnCount: 3,
        columns: [
          { index: 0, width: '15%', label: '侧边栏' },
          { index: 1, width: '25%', label: '左列', fill: fillColumn.value.left },
          { index: 2, width: '60%', label: '右列', fill: fillColumn.value.center }
        ],
        leftColumnWidth: leftColumnWidth.value
      },
      dataSource: pageConfig.dataSource || {
        exampleJsonText: '',
        customFieldRules: []
      }
    }

    console.log('Saving config:', config)
    await saveAnnotationPageConfig(projectId.value, config)

    // 更新 localStorage，以便下次打开预览时使用最新配置
    localStorage.setItem('annotation-preview-config', JSON.stringify(config))

    alert('布局已保存')
  } catch (e: any) {
    console.error('Save layout error:', e)
    alert('保存失败: ' + (e.message || '未知错误'))
  } finally {
    isSavingLayout.value = false
  }
}

const submitConfirm = ref(false)

const handleSubmit = () => {
  submitConfirm.value = true
}

const confirmSubmit = async () => {
  submitConfirm.value = false
  try {
    alert('任务已提交')
    router.push('/tasks')
  } catch (e) {
    alert('提交失败')
  }
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
    return
  }

  if (e.ctrlKey && e.key === 's') {
    e.preventDefault()
    handleSave()
  }
}

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

      <!-- 主内容区域 -->
      <div class="annotation-content">
        <LayoutContainer
          ref="layoutContainerRef"
          :layout="layout"
          :readonly="false"
          :left-column-width="leftColumnWidth"
          @update:left-column-width="handleLeftColumnWidthChange"
        >
          <template #left>
            <div class="column-content" :class="{ fill: fillColumn.left }">
              <template v-for="panel in layout.left.panels" :key="panel.id">
                <div class="panel-wrapper" :class="{ fill: fillColumn.left }">
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
                      :config="(panel as any).config"
                      :show-title="false"
                    />
                    <!-- 单选组件 -->
                    <RadioSelector
                      v-else-if="panel.toolId === 'RadioSelector'"
                      :config="(panel as any).config"
                      :show-title="false"
                    />
                    <!-- 文本输入 -->
                    <TextInput
                      v-else-if="panel.toolId === 'TextInput'"
                      :config="(panel as any).config"
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

          <template #center>
            <div class="column-content" :class="{ fill: fillColumn.center }">
              <template v-for="panel in layout.center.panels" :key="panel.id">
                <div class="panel-wrapper" :class="{ fill: fillColumn.center }">
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
                      :config="(panel as any).config"
                      :show-title="false"
                    />
                    <!-- 单选组件 -->
                    <RadioSelector
                      v-else-if="panel.toolId === 'RadioSelector'"
                      :config="(panel as any).config"
                      :show-title="false"
                    />
                    <!-- 文本输入 -->
                    <TextInput
                      v-else-if="panel.toolId === 'TextInput'"
                      :config="(panel as any).config"
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
        <button class="btn-footer btn-save" @click="handleSave" :disabled="isSaving || !taskData[currentIndex]">
          ✓ 保存
        </button>
        <button class="btn-footer btn-next" @click="currentIndex < taskData.length - 1 && currentIndex++" :disabled="currentIndex >= taskData.length - 1">
          下一条 →
        </button>
      </template>
    </div>

    <!-- 提交确认对话框 -->
    <div v-if="submitConfirm" class="dialog-overlay" @click.self="submitConfirm = false">
      <div class="dialog">
        <div class="dialog-title">确认提交</div>
        <div class="dialog-content">确定要提交此任务吗？提交后将无法继续编辑。</div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="submitConfirm = false">取消</button>
          <button class="btn btn-primary" @click="confirmSubmit">确定</button>
        </div>
      </div>
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
  flex-shrink: 0;  /* 默认不拉伸 - 不平铺 */
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
  flex-shrink: 0;  /* 默认不拉伸 */
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

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  padding: 16px 20px;
  border-bottom: 1px solid #E5E7EB;
}

.dialog-content {
  padding: 20px;
  color: #4B5563;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #E5E7EB;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-primary {
  background: #165DFF;
  color: white;
}

.btn-primary:hover {
  background: #0E42D2;
}

.btn-secondary {
  background: #F3F4F6;
  color: #374151;
}

.btn-secondary:hover {
  background: #E5E7EB;
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