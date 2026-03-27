<script setup lang="ts">
/**
 * 标注页面配置器
 *
 * 实现设计文档中的流程：
 * 1. 上传示例 JSON → 自动提取字段
 * 2. 拖拽模块到画布
 * 3. 配置字段绑定（支持智能推荐）
 * 4. 保存配置
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import draggable from 'vuedraggable'
import { getAllModules, getModuleById } from '@/composables/useAnnotationModuleRegistry'
import { extractFieldsWithRules, smartBind, resolveFieldBinding, applyCustomFieldRules } from '@/composables/useDataSourceParser'
import { getAnnotationPageConfig, saveAnnotationPageConfig } from '@/api/project'
import type { ModuleDefinition, ModuleInstance, PageConfig, ParsedField, CustomFieldRule, LayoutConfig } from '@/types/annotation-module'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))

// 步骤控制
const currentStep = ref(1)

// 加载项目已有配置
const existingConfig = ref<PageConfig | null>(null)
const configLoading = ref(false)

// 步骤 1: 数据源配置
const exampleJsonText = ref('')
const parsedFields = ref<ParsedField[]>([])
const exampleData = ref<any>(null)
const customFieldRules = ref<CustomFieldRule[]>([])

// 自定义字段规则表单
const customRuleFormVisible = ref(false)
const customRuleName = ref('')
const customRuleType = ref<'path' | 'regex'>('path')
const customRulePath = ref('')
const customRuleRegex = ref('')
const customRuleRegexSource = ref('')

// 步骤 2: 模块配置（固定三列：侧边栏 15%, 左列 25%, 右列 60%）
const columnWidths = ref<number[]>([25, 60])  // 左列和右列的百分比（侧边栏固定 15%）
const columnLabels = ref<string[]>(['左列', '右列'])

// 步骤 3: 模块配置
const availableModules = ref<ModuleDefinition[]>(getAllModules())
const placedModules = ref<ModuleInstance[]>([])
const selectedModule = ref<ModuleInstance | null>(null)

// 组件市场中的模块（始终显示所有可用模块，支持重复添加）
const marketModules = computed<ModuleDefinition[]>(() => {
  return availableModules.value
})

// 保存当前从组件市场拖拽的模块定义
const draggingModule = ref<ModuleDefinition | null>(null)

// 组件市场拖拽开始
const handleMarketDragStart = (event: any) => {
  const index = event.oldIndex
  if (index !== undefined && marketModules.value[index]) {
    draggingModule.value = marketModules.value[index]
  }
}

// 步骤 4: 预览与保存
const previewData = ref<any>(null)

// 加载已有配置
const loadExistingConfig = async () => {
  configLoading.value = true
  try {
    existingConfig.value = await getAnnotationPageConfig(projectId.value)
    if (existingConfig.value && existingConfig.value.modules) {
      placedModules.value = existingConfig.value.modules || []
      ElMessage.success('加载已有配置成功')
    }
  } catch (e: any) {
    // 如果没有配置，忽略错误
    if (e.response?.status !== 404) {
      ElMessage.warning('加载配置失败')
    }
  } finally {
    configLoading.value = false
  }
}

// 上传示例 JSON
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const json = JSON.parse(e.target?.result as string)
      exampleData.value = json
      exampleJsonText.value = JSON.stringify(json, null, 2)
      parsedFields.value = extractFieldsWithRules(json, customFieldRules.value)
      ElMessage.success('JSON 解析成功')
    } catch (err) {
      ElMessage.error('JSON 格式错误')
    }
  }
  reader.readAsText(file)
}

// 手动粘贴 JSON
const handleJsonPaste = () => {
  try {
    const json = JSON.parse(exampleJsonText.value)
    exampleData.value = json
    parsedFields.value = extractFieldsWithRules(json, customFieldRules.value)
    ElMessage.success('JSON 解析成功')
  } catch (err) {
    ElMessage.error('JSON 格式错误')
  }
}

// 打开添加自定义规则对话框
const openAddCustomRuleDialog = () => {
  customRuleName.value = ''
  customRuleType.value = 'path'
  customRulePath.value = ''
  customRuleRegex.value = ''
  customRuleRegexSource.value = ''
  customRuleFormVisible.value = true
}

// 添加自定义规则
const handleAddCustomRule = () => {
  if (!customRuleName.value) {
    ElMessage.error('请输入规则名称')
    return
  }

  if (customRuleType.value === 'path' && !customRulePath.value) {
    ElMessage.error('请输入 JSONPath')
    return
  }

  if (customRuleType.value === 'regex' && (!customRuleRegex.value || !customRuleRegexSource.value)) {
    ElMessage.error('请输入正则表达式和源字段')
    return
  }

  const newRule: CustomFieldRule = {
    name: customRuleName.value,
    ruleType: customRuleType.value,
    path: customRuleType.value === 'path' ? customRulePath.value : undefined,
    regex: customRuleType.value === 'regex' ? customRuleRegex.value : undefined,
    regexSource: customRuleType.value === 'regex' ? customRuleRegexSource.value : undefined
  }

  customFieldRules.value.push(newRule)

  // 重新解析字段
  if (exampleData.value) {
    parsedFields.value = extractFieldsWithRules(exampleData.value, customFieldRules.value)
  }

  customRuleFormVisible.value = false
  ElMessage.success('自定义规则添加成功')
}

// 删除自定义规则
const handleRemoveCustomRule = (index: number) => {
  customFieldRules.value.splice(index, 1)
  if (exampleData.value) {
    parsedFields.value = extractFieldsWithRules(exampleData.value, customFieldRules.value)
  }
  ElMessage.success('规则已删除')
}

// 重新解析 JSON（当自定义规则变化时）
const reparseJson = () => {
  if (exampleData.value) {
    parsedFields.value = extractFieldsWithRules(exampleData.value, customFieldRules.value)
    ElMessage.success('字段已重新解析')
  }
}

// 删除模块
const removeModule = (moduleId: string) => {
  placedModules.value = placedModules.value.filter(m => m.id !== moduleId)
  if (selectedModule.value?.id === moduleId) {
    selectedModule.value = null
  }
}

// 选择模块
const selectModule = (module: ModuleInstance) => {
  selectedModule.value = module
}

// 自动推荐字段绑定
const autoBindFields = () => {
  if (!selectedModule.value || !exampleData.value) return

  const moduleDef = getModuleById(selectedModule.value.type)
  if (!moduleDef) return

  selectedModule.value.fieldBindings = smartBind(moduleDef, exampleData.value)
  ElMessage.success('字段绑定已自动推荐')
}

// 获取推荐字段（用于下拉框）
const getRecommendedFields = (fieldName: string): ParsedField[] => {
  if (!selectedModule.value || !exampleData.value) return []

  const moduleDef = getModuleById(selectedModule.value.type)
  if (!moduleDef) return []

  const mappingFn = moduleDef.fieldMapping[fieldName]
  if (!mappingFn) return []

  const mappedValue = mappingFn(exampleData.value)
  if (!mappedValue) return []

  const path = findPathByValue(exampleData.value, mappedValue)
  if (!path) return []

  return parsedFields.value.filter(f => f.path === path)
}

// 查找路径（辅助函数）
const findPathByValue = (data: any, target: any): string | null => {
  for (const [key, val] of Object.entries(data)) {
    if (val === target) return key
    if (typeof val === 'object' && val !== null) {
      const path = findPathByValue(val, target)
      if (path) return `${key}.${path}`
    }
  }
  return null
}

// 更新字段绑定
const updateFieldBinding = (fieldName: string, path: string) => {
  if (!selectedModule.value) return
  selectedModule.value.fieldBindings[fieldName] = path
}

// 获取模块在画布中的位置（支持动态列索引）
const getModulesInDynamicColumn = (colIndex: number) => {
  return placedModules.value.filter(m => m.col === colIndex)
}

// 保存配置
const handleSave = async () => {
  if (placedModules.value.length === 0) {
    ElMessage.warning('请至少添加一个模块')
    return
  }

  try {
    const config: PageConfig = {
      modules: placedModules.value,
      layout: {
        columnCount: 3,
        columns: [
          { index: 0, width: '15%', label: '侧边栏' },
          { index: 1, width: `${columnWidths.value[0]}%`, label: columnLabels.value[0] },
          { index: 2, width: `${columnWidths.value[1]}%`, label: columnLabels.value[1] }
        ]
      }
    }

    // 调用 API 保存配置
    await saveAnnotationPageConfig(projectId.value, config)

    await ElMessageBox.alert('配置已保存', '成功', {
      confirmButtonText: '确定'
    })

    router.push(`/projects/${projectId.value}`)
  } catch (err: any) {
    let errorMsg = '保存失败'
    if (err.response?.data?.detail) {
      errorMsg = err.response.data.detail
    }
    ElMessage.error(errorMsg)
  }
}

// 打开预览页面
const openPreview = async () => {
  if (placedModules.value.length === 0) {
    ElMessage.warning('请先添加模块')
    return
  }

  // 保存配置到 sessionStorage 供预览页面使用
  const previewConfig: PageConfig = {
    modules: placedModules.value,
    layout: {
      columnCount: 3,
      columns: [
        { index: 0, width: '15%', label: '侧边栏' },
        { index: 1, width: `${columnWidths.value[0]}%`, label: columnLabels.value[0] },
        { index: 2, width: `${columnWidths.value[1]}%`, label: columnLabels.value[1] }
      ]
    }
  }
  sessionStorage.setItem('annotation-preview-config', JSON.stringify(previewConfig))
  sessionStorage.setItem('annotation-preview-data', JSON.stringify(exampleData.value))

  // 在新窗口打开预览页面
  const previewUrl = `/projects/${projectId.value}/preview`
  window.open(previewUrl, '_blank')

  ElMessage.success({
    message: '已打开测试页面，使用示例数据进行测试',
    duration: 3000
  })
}

// 上一步/下一步
const prevStep = () => {
  if (currentStep.value > 1) currentStep.value--
}

const nextStep = () => {
  if (currentStep.value < 3) currentStep.value++
}

// 列宽调整相关
const canvasRef = ref<HTMLElement | null>(null)
const isResizing = ref(false)
const resizingColumnIndex = ref(-1)
const startX = ref(0)
const startWidths = ref<number[]>([...columnWidths.value])

// 获取列样式
const getColumnStyle = (index: number) => {
  return {
    width: `${columnWidths.value[index]}%`,
    flex: `0 0 ${columnWidths.value[index]}%`
  }
}

// 开始调整列宽
const handleResizerMouseDown = (e: MouseEvent, columnIndex: number) => {
  startResizing(e, columnIndex)
}

const startResizing = (e: MouseEvent, columnIndex: number) => {
  isResizing.value = true
  resizingColumnIndex.value = columnIndex
  startX.value = e.clientX
  startWidths.value = [...columnWidths.value]

  document.addEventListener('mousemove', handleResizing)
  document.addEventListener('mouseup', stopResizing)
  e.preventDefault()
  e.stopPropagation()
}

const handleResizing = (e: MouseEvent) => {
  if (!isResizing.value || !canvasRef.value) return

  const deltaX = e.clientX - startX.value
  const containerWidth = canvasRef.value.offsetWidth
  const deltaPercent = (deltaX / containerWidth) * 100

  // 调整左列（索引 0）和右列（索引 1）
  let newLeftPercent = startWidths.value[0] + deltaPercent
  let newRightPercent = startWidths.value[1] - deltaPercent

  // 应用最小/最大限制
  newLeftPercent = Math.max(15, Math.min(50, newLeftPercent))
  newRightPercent = Math.max(15, Math.min(50, newRightPercent))

  // 确保总和为 85（因为侧边栏占 15%）
  const total = newLeftPercent + newRightPercent
  newLeftPercent = (newLeftPercent / total) * 85
  newRightPercent = (newRightPercent / total) * 85

  columnWidths.value[0] = newLeftPercent
  columnWidths.value[1] = newRightPercent

  e.preventDefault()
}

const stopResizing = () => {
  isResizing.value = false
  resizingColumnIndex.value = -1
  document.removeEventListener('mousemove', handleResizing)
  document.removeEventListener('mouseup', stopResizing)
}

// 获取指定列的模块
const getModulesInColumn = (colIndex: number) => {
  return placedModules.value.filter(m => m.col === colIndex)
}

// 每个列的模块列表（用于 vuedraggable，使用 computed 带 setter）
const leftColumnModules = computed<ModuleInstance[]>({
  get: () => placedModules.value.filter(m => m.col === 1),
  set: (val) => {
    // 保留非左列的模块
    const otherModules = placedModules.value.filter(m => m.col !== 1)
    // 更新左列模块的 col 属性
    val.forEach(m => m.col = 1)
    placedModules.value = [...otherModules, ...val]
  }
})

const rightColumnModules = computed<ModuleInstance[]>({
  get: () => placedModules.value.filter(m => m.col === 2),
  set: (val) => {
    const otherModules = placedModules.value.filter(m => m.col !== 2)
    val.forEach(m => m.col = 2)
    placedModules.value = [...otherModules, ...val]
  }
})

// 克隆模块（从组件市场拖拽时调用）
const cloneModule = (module: ModuleDefinition) => {
  // 直接返回原始对象，vuedraggable 会处理克隆
  // 关键：保留 id 和 name 用于后续识别
  return {
    _isClone: true,
    id: module.id,
    name: module.name,
    description: module.description
  }
}

// 处理模块添加（从组件市场拖拽）
const handleModuleAdd = (event: any, colIndex: number) => {
  // 使用之前保存的模块定义
  const moduleDef = draggingModule.value
  if (!moduleDef) {
    return
  }

  const moduleType = moduleDef.id
  const moduleName = moduleDef.name || '未知模块'

  // 创建新的模块实例
  const newModule: ModuleInstance = {
    id: `${moduleType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type: moduleType,
    col: colIndex,
    row: 1,
    width: colIndex === 2 ? '60%' : '30%',
    height: '100%',
    fieldBindings: {},
    props: {}
  }

  // 尝试智能绑定字段（如果有示例数据）
  const moduleDefFromRegistry = getModuleById(moduleType)
  if (moduleDefFromRegistry && exampleData.value) {
    newModule.fieldBindings = smartBind(moduleDefFromRegistry, exampleData.value)
    newModule.props = { ...moduleDefFromRegistry.defaultProps }
  }

  // 添加到已放置模块列表
  placedModules.value.push(newModule)
  selectedModule.value = newModule

  // 清除拖拽状态
  draggingModule.value = null

  ElMessage.success({
    message: `已添加"${moduleName}"`,
    duration: 1500
  })
}

onMounted(() => {
  loadExistingConfig()
})
</script>

<template>
  <div class="project-configurator">
    <el-card>
      <template #header>
        <div class="configurator-header">
          <h2>标注页面配置</h2>
          <el-button @click="$router.push(`/projects/${projectId}`)">返回</el-button>
        </div>
      </template>

      <!-- 步骤条 -->
      <el-steps :active="currentStep - 1" align-center style="margin-bottom: 24px">
        <el-step title="数据源配置" />
        <el-step title="模块配置" />
        <el-step title="预览保存" />
      </el-steps>

      <!-- 步骤 1: 数据源配置 -->
      <div v-show="currentStep === 1" class="step-content">
        <h3>上传示例 JSON 数据</h3>
        <p class="help-text">上传一条典型的 JSON 数据，系统将自动提取可用字段</p>

        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          accept=".json"
          :on-change="handleFileUpload"
        >
          <el-button type="primary">📤 上传 JSON 文件</el-button>
        </el-upload>

        <el-divider>或</el-divider>

        <el-input
          v-model="exampleJsonText"
          type="textarea"
          :rows="10"
          placeholder="粘贴 JSON 数据..."
        />
        <el-button type="primary" @click="handleJsonPaste" style="margin-top: 8px">
          解析 JSON
        </el-button>

        <!-- 自定义字段规则 -->
        <el-divider>自定义字段规则</el-divider>
        <div class="custom-rules-section">
          <div class="rules-header">
            <span>已配置 {{ customFieldRules.length }} 条规则</span>
            <el-button type="primary" size="small" @click="openAddCustomRuleDialog">
              + 添加规则
            </el-button>
          </div>

          <el-table v-if="customFieldRules.length > 0" :data="customFieldRules" size="small" style="margin-top: 12px">
            <el-table-column prop="name" label="规则名称" width="150" />
            <el-table-column label="规则类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="row.ruleType === 'path' ? 'success' : 'warning'">
                  {{ row.ruleType === 'path' ? 'JSONPath' : '正则' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="JSONPath" width="200">
              <template #default="{ row }">
                <span v-if="row.ruleType === 'path'">{{ row.path }}</span>
                <span v-else style="color: #999">-</span>
              </template>
            </el-table-column>
            <el-table-column label="正则表达式" width="200">
              <template #default="{ row }">
                <span v-if="row.ruleType === 'regex'">{{ row.regex }}</span>
                <span v-else style="color: #999">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row, $index }">
                <el-button link type="danger" size="small" @click="handleRemoveCustomRule($index)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-else description="暂无自定义规则" :image-size="80" />
        </div>

        <!-- 字段列表 -->
        <div v-if="parsedFields.length > 0" class="fields-preview">
          <h4>提取的字段（{{ parsedFields.length }} 个）</h4>
          <el-table :data="parsedFields" size="small" max-height="300">
            <el-table-column prop="path" label="字段路径" width="200" />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.path?.startsWith('custom:') ? 'warning' : 'info'">
                  {{ row.type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="示例值/预览" min-width="200">
              <template #default="{ row }">
                <span v-if="row.sampleValue !== undefined">
                  {{ String(row.sampleValue).slice(0, 50) }}
                </span>
                <span v-else-if="row.preview" style="color: #999">
                  {{ row.preview }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 步骤 2: 模块配置 -->
      <div v-show="currentStep === 2" class="step-content">
        <div class="config-layout">
          <!-- 左侧：画布 -->
          <div class="canvas-area">
            <h4>画布预览</h4>
            <p class="help-text">拖拽模块调整顺序，或移动到其他列。鼠标移动到列边界可拖拽调整列宽。</p>
            <div class="canvas" ref="canvasRef">
              <!-- 侧边栏固定在最左侧（15% 宽度） -->
              <div class="canvas-col sidebar-col" :style="{ width: '15%', minWidth: '180px' }">
                <div class="column-header">
                  侧边栏
                  <span class="column-count">(固定)</span>
                </div>
                <div class="sidebar-fixed">
                  <div class="module-block sidebar-module">
                    <div class="module-avatar">侧</div>
                    <div class="module-info">
                      <div class="module-name">标注任务列表</div>
                      <div class="module-desc">显示任务列表和进度（系统自动添加）</div>
                    </div>
                  </div>
                  <p class="sidebar-tip">此组件为系统默认添加，无需手动配置</p>
                </div>
              </div>

              <!-- 左列（可调整，默认 25%） -->
              <div class="canvas-col resizable-col" :style="getColumnStyle(0)">
                <div class="column-header">
                  {{ columnLabels[0] }}
                  <span class="column-width">{{ columnWidths[0].toFixed(1) }}%</span>
                </div>
                <draggable
                  :list="leftColumnModules"
                  :group="{ name: 'modules', pull: false, put: true }"
                  :animation="200"
                  :empty-insert-threshold="30"
                  item-key="id"
                  class="draggable-list"
                  @add="(e: any) => handleModuleAdd(e, 1)"
                >
                  <template #item="{ element: module }">
                    <div
                      class="module-block"
                      :class="{ selected: selectedModule?.id === module.id }"
                      @click="selectModule(module)"
                    >
                      <div class="module-avatar">{{ getModuleById(module.type)?.name?.charAt(0) || '模' }}</div>
                      <div class="module-info">
                        <div class="module-name">{{ getModuleById(module.type)?.name }}</div>
                        <div class="module-desc">{{ getModuleById(module.type)?.description }}</div>
                      </div>
                      <div class="drag-handle">
                        <el-icon><rank /></el-icon>
                      </div>
                      <el-button
                        link
                        type="danger"
                        size="small"
                        @click.stop="removeModule(module.id)"
                        class="remove-btn"
                      >×</el-button>
                    </div>
                  </template>
                  <template #empty>
                    <div class="empty-column">
                      拖拽组件到此处
                    </div>
                  </template>
                </draggable>
              </div>

              <!-- 左列和右列之间的拖拽手柄 -->
              <div class="column-resizer" @mousedown="(e) => handleResizerMouseDown(e, 0)">
                <div class="resizer-handle"></div>
              </div>

              <!-- 右列（可调整，默认 60%） -->
              <div class="canvas-col resizable-col" :style="getColumnStyle(1)">
                <div class="column-header">
                  {{ columnLabels[1] }}
                  <span class="column-width">{{ columnWidths[1].toFixed(1) }}%</span>
                </div>
                <draggable
                  :list="rightColumnModules"
                  :group="{ name: 'modules', pull: false, put: true }"
                  :animation="200"
                  :empty-insert-threshold="30"
                  item-key="id"
                  class="draggable-list"
                  @add="(e: any) => handleModuleAdd(e, 2)"
                >
                  <template #item="{ element: module }">
                    <div
                      class="module-block"
                      :class="{ selected: selectedModule?.id === module.id }"
                      @click="selectModule(module)"
                    >
                      <div class="module-avatar">{{ getModuleById(module.type)?.name?.charAt(0) || '模' }}</div>
                      <div class="module-info">
                        <div class="module-name">{{ getModuleById(module.type)?.name }}</div>
                        <div class="module-desc">{{ getModuleById(module.type)?.description }}</div>
                      </div>
                      <div class="drag-handle">
                        <el-icon><rank /></el-icon>
                      </div>
                      <el-button
                        link
                        type="danger"
                        size="small"
                        @click.stop="removeModule(module.id)"
                        class="remove-btn"
                      >×</el-button>
                    </div>
                  </template>
                  <template #empty>
                    <div class="empty-column">
                      拖拽组件到此处
                    </div>
                  </template>
                </draggable>
              </div>
            </div>
          </div>

          <!-- 右侧：属性面板 -->
          <div class="props-panel" v-if="selectedModule">
            <h4>模块属性</h4>
            <el-form label-width="100px" size="small">
              <el-form-item label="模块类型">
                <span>{{ getModuleById(selectedModule.type)?.name }}</span>
              </el-form-item>

              <el-divider>数据绑定</el-divider>

              <!-- 字段绑定 -->
              <div v-for="(fieldSchema, fieldName) in getModuleById(selectedModule.type)?.schema.fields"
                   :key="fieldName"
                   class="field-binding-item"
              >
                <label>
                  {{ fieldSchema.label }}
                  <span v-if="fieldSchema.required" class="required">*</span>
                </label>

                <div class="binding-actions">
                  <el-select
                    v-model="selectedModule.fieldBindings[fieldName]"
                    placeholder="选择字段"
                    filterable
                    style="width: 100%"
                  >
                    <optgroup
                      v-if="getRecommendedFields(fieldName).length > 0"
                      label="推荐字段"
                    >
                      <el-option
                        v-for="f in getRecommendedFields(fieldName)"
                        :key="f.path"
                        :label="f.path"
                        :value="f.path"
                      />
                    </optgroup>
                    <optgroup label="所有字段">
                      <el-option
                        v-for="f in parsedFields"
                        :key="f.path"
                        :label="`${f.path} (${f.type})`"
                        :value="f.path"
                      />
                    </optgroup>
                  </el-select>
                </div>
              </div>

              <el-button type="primary" @click="autoBindFields" style="width: 100%; margin-top: 16px">
                🤖 智能推荐
              </el-button>
            </el-form>
          </div>

          <div v-else class="props-panel empty">
            <p>点击画布中的模块配置属性</p>
          </div>
        </div>

        <!-- 组件市场 -->
        <h3 style="margin-top: 24px">组件市场</h3>
        <p class="help-text">拖拽组件到画布，或点击画布中的模块配置属性</p>
        <draggable
          :list="marketModules"
          :group="{ name: 'modules', pull: 'clone', put: false }"
          :sort="false"
          :animation="200"
          item-key="id"
          class="component-market"
          :clone="cloneModule"
          @start="handleMarketDragStart"
        >
          <template #item="{ element: module }">
            <div class="component-card">
              <div class="component-avatar">{{ module.name.charAt(0) }}</div>
              <div class="component-info">
                <h4>{{ module.name }}</h4>
                <p class="component-desc">{{ module.description }}</p>
              </div>
            </div>
          </template>
        </draggable>
      </div>

      <!-- 步骤 3: 预览保存 -->
      <div v-show="currentStep === 3" class="step-content">
        <h3>配置预览</h3>
        <pre class="config-preview">{{ JSON.stringify({ modules: placedModules }, null, 2) }}</pre>

        <h3>数据预览</h3>
        <p class="help-text">使用示例数据模拟运行时效果</p>
        <div v-if="exampleData" class="data-preview">
          <el-table :data="placedModules" size="small">
            <el-table-column prop="type" label="模块类型" width="150">
              <template #default="{ row }">
                {{ getModuleById(row.type)?.name }}
              </template>
            </el-table-column>
            <el-table-column label="绑定数据预览" min-width="400">
              <template #default="{ row }">
                <div v-for="(path, field) in row.fieldBindings" :key="field" class="preview-row">
                  <strong>{{ field }}:</strong>
                  <code>{{ resolveFieldBinding(exampleData, path) }}</code>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 测试按钮 -->
        <el-divider>测试标注页面</el-divider>
        <p class="help-text">在保存前测试标注页面效果（使用示例数据）</p>
        <el-button type="success" @click="openPreview">
          🚀 打开测试页面
        </el-button>
      </div>

      <!-- 底部按钮 -->
      <div class="configurator-footer">
        <el-button @click="prevStep" :disabled="currentStep === 1">上一步</el-button>
        <el-button
          v-if="currentStep < 3"
          type="primary"
          @click="nextStep"
          :disabled="currentStep === 1 && parsedFields.length === 0"
        >
          下一步
        </el-button>
        <el-button
          v-else
          type="primary"
          @click="handleSave"
        >
          保存配置
        </el-button>
      </div>
    </el-card>

    <!-- 添加自定义字段规则对话框 -->
    <el-dialog v-model="customRuleFormVisible" title="添加自定义字段规则" width="500px">
      <el-form label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="customRuleName" placeholder="如：提取 ID" />
        </el-form-item>
        <el-form-item label="规则类型" required>
          <el-radio-group v-model="customRuleType">
            <el-radio value="path">JSONPath</el-radio>
            <el-radio value="regex">正则表达式</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- JSONPath 配置 -->
        <template v-if="customRuleType === 'path'">
          <el-form-item label="JSONPath" required>
            <el-input v-model="customRulePath" placeholder="如：data.items[0].id" />
            <p class="form-tip">支持格式：field, field.subfield, field[0], field[0].subfield</p>
          </el-form-item>
        </template>

        <!-- 正则表达式配置 -->
        <template v-if="customRuleType === 'regex'">
          <el-form-item label="源字段" required>
            <el-select v-model="customRuleRegexSource" placeholder="选择源字段" filterable style="width: 100%">
              <el-option
                v-for="field in parsedFields.filter(f => !f.path?.startsWith('custom:'))"
                :key="field.path"
                :label="field.path"
                :value="field.path"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="正则表达式" required>
            <el-input v-model="customRuleRegex" placeholder="如：id:(\d+)" />
            <p class="form-tip">第一个捕获组将作为提取结果</p>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="customRuleFormVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddCustomRule">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.project-configurator {
  .configurator-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .step-content {
    min-height: 400px;

    h3 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
    }

    .help-text {
      color: #999;
      font-size: 13px;
      margin-bottom: 16px;
    }
  }

  .fields-preview {
    margin-top: 24px;
  }

  .custom-rules-section {
    margin-top: 16px;

    .rules-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 14px;
      font-weight: 500;
    }
  }

  .form-tip {
    margin: 4px 0 0 0;
    font-size: 12px;
    color: #999;
  }

  .component-market {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 16px;

    .component-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: white;
      border: 1px solid #e3e5e7;
      border-radius: 8px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.2s;
      min-height: 140px;

      &:hover {
        border-color: #fb7299;
        box-shadow: 0 4px 12px rgba(251, 114, 153, 0.15);
        transform: translateY(-2px);
      }

      .component-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #fb7299 0%, #ff9eb5 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 12px;
        flex-shrink: 0;
      }

      .component-info {
        text-align: center;

        h4 {
          margin: 0 0 6px 0;
          font-size: 14px;
          font-weight: 600;
          color: #212121;
        }

        .component-desc {
          margin: 0;
          font-size: 12px;
          color: #9499a0;
          line-height: 1.5;
        }
      }
    }
  }

  .config-layout {
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 16px;
  }

  .canvas-area {
    .canvas {
      display: flex;
      gap: 0;
      height: 500px;
      background: #f4f5f7;
      padding: 8px;
      border-radius: 8px;
      position: relative;
    }

    .canvas-col {
      display: flex;
      flex-direction: column;
      gap: 8px;
      transition: width 0.1s ease-out;

      &.sidebar-col {
        flex-shrink: 0;
      }

      &.resizable-col {
        flex-shrink: 0;
      }

      .column-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        font-weight: 600;
        color: #666;
        padding: 4px 8px;
        background: #e9ecef;
        border-radius: 4px;

        .column-count {
          font-size: 11px;
          color: #999;
        }

        .column-width {
          font-size: 11px;
          color: #999;
          font-weight: normal;
        }
      }

      .draggable-list {
        flex: 1;
        min-height: 100px;
      }

      .empty-column {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100px;
        border: 2px dashed #d0d7de;
        border-radius: 8px;
        color: #999;
        font-size: 13px;
      }
    }

    // 列调整手柄
    .column-resizer {
      width: 8px;
      margin-left: -8px;
      position: relative;
      z-index: 10;
      cursor: col-resize;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: background 0.2s;

      &:hover {
        background: rgba(251, 114, 153, 0.2);
      }

      &:active {
        background: rgba(251, 114, 153, 0.3);
      }
    }

    .resizer-handle {
      width: 4px;
      height: 24px;
      background: #d0d7de;
      border-radius: 2px;
      transition: all 0.2s;

      .column-resizer:hover &,
      .column-resizer:active & {
        background: #fb7299;
        height: 32px;
      }
    }

    .module-block {
      display: flex;
      align-items: center;
      gap: 12px;
      background: white;
      border: 2px solid #e3e5e7;
      border-radius: 8px;
      padding: 12px;
      cursor: pointer;
      transition: all 0.2s;
      position: relative;
      margin-bottom: 8px;

      &:hover {
        border-color: #fb7299;
      }

      &.selected {
        border-color: #fb7299;
        background: rgba(251, 114, 153, 0.05);
      }

      .module-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #fb7299 0%, #ff9eb5 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: 600;
        flex-shrink: 0;
      }

      .module-info {
        flex: 1;
        min-width: 0;

        .module-name {
          font-size: 14px;
          font-weight: 600;
          color: #212121;
          margin-bottom: 4px;
        }

        .module-desc {
          font-size: 12px;
          color: #9499a0;
        }
      }

      .drag-handle {
        display: flex;
        align-items: center;
        color: #999;
        cursor: grab;
        flex-shrink: 0;

        &:active {
          cursor: grabbing;
        }
      }

      .module-bindings {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }

      .binding-tag {
        background: #f4f5f7;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        color: #666;
      }

      .remove-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        opacity: 0;
        transition: opacity 0.2s;
      }

      &:hover .remove-btn {
        opacity: 1;
      }
    }

    .sidebar-module {
      .module-avatar {
        background: linear-gradient(135deg, #00aeec 0%, #0096c7 100%);
      }
    }

    .sidebar-fixed {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .sidebar-tip {
      font-size: 12px;
      color: #9499a0;
      text-align: center;
      padding: 8px;
      background: #f4f5f7;
      border-radius: 4px;
    }
  }

  .props-panel {
    background: white;
    border: 1px solid #e3e5e7;
    border-radius: 8px;
    padding: 16px;
    height: fit-content;

    &.empty {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #999;
    }

    .field-binding-item {
      margin-bottom: 12px;

      label {
        display: block;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 6px;

        .required {
          color: #fb7299;
          margin-left: 4px;
        }
      }
    }
  }

  .config-preview {
    background: #f4f5f7;
    padding: 16px;
    border-radius: 8px;
    font-family: monospace;
    font-size: 12px;
    max-height: 300px;
    overflow: auto;
  }

  .data-preview {
    .preview-row {
      display: flex;
      gap: 8px;
      padding: 4px 0;
      border-bottom: 1px solid #f0f0f0;

      strong {
        min-width: 100px;
        color: #666;
      }

      code {
        background: #f4f5f7;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
      }
    }
  }

  .configurator-footer {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 24px;
  }
}
</style>

<style lang="scss">
// 全局样式：隐藏拖拽时的 ghost 元素
.sortable-ghost {
  opacity: 0 !important;

  * {
    visibility: hidden !important;
  }
}
</style>
