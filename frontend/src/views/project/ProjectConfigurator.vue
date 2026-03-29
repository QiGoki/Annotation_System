<script setup lang="ts">
/**
 * 标注页面配置器 v3 - StepFun风格
 *
 * 使用新版配置系统
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import { getAllModules, getModuleById } from '@/composables/useAnnotationModuleRegistry'
import { extractFieldsWithRules } from '@/composables/useDataSourceParser'
import { getAnnotationPageConfig, saveAnnotationPageConfig } from '@/api/project'
import ModuleConfigEditor from '@/components/annotation/ModuleConfigEditor.vue'
import type { ModuleInstance, PageConfig, ParsedField, CustomFieldRule } from '@/types/annotation-module'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))

const currentStep = ref(1)
const existingConfig = ref<PageConfig | null>(null)
const configLoading = ref(false)

const exampleJsonText = ref('')
const parsedFields = ref<ParsedField[]>([])
const exampleData = ref<any>(null)
const customFieldRules = ref<CustomFieldRule[]>([])

const customRuleFormVisible = ref(false)
const customRuleName = ref('')
const customRuleType = ref<'path' | 'regex'>('path')
const customRulePath = ref('')
const customRuleRegex = ref('')
const customRuleRegexSource = ref('')

const availableModules = getAllModules()
const placedModules = ref<ModuleInstance[]>([])
const selectedModuleId = ref<string | null>(null)

// 每列是否平铺
const fillColumn = ref({ left: false, right: false })

// 左列宽度（从已保存配置加载）
const savedLeftColumnWidth = ref<number | undefined>(undefined)

const selectedModule = computed(() =>
  placedModules.value.find(m => m.id === selectedModuleId.value) || null
)

const marketModules = computed(() => availableModules)
const draggingModule = ref<string | null>(null)

const handleMarketDragStart = (event: any) => {
  const index = event.oldIndex
  if (index !== undefined && marketModules.value[index]) {
    draggingModule.value = marketModules.value[index].id
  }
}

const loadExistingConfig = async () => {
  configLoading.value = true
  try {
    existingConfig.value = await getAnnotationPageConfig(projectId.value)
    if (existingConfig.value) {
      // 加载模块
      if (existingConfig.value.modules) {
        placedModules.value = existingConfig.value.modules
      }
      // 加载数据源配置
      if (existingConfig.value.dataSource) {
        const ds = existingConfig.value.dataSource
        exampleJsonText.value = ds.exampleJsonText || ''
        customFieldRules.value = ds.customFieldRules || []
        // 重新解析字段
        if (exampleJsonText.value) {
          try {
            const json = JSON.parse(exampleJsonText.value)
            exampleData.value = json
            parsedFields.value = extractFieldsWithRules(json, customFieldRules.value)
          } catch (e) {
            console.warn('无法解析保存的 JSON')
          }
        }
      }
      // 加载平铺配置
      if (existingConfig.value.layout?.columns) {
        const leftCol = existingConfig.value.layout.columns.find(c => c.index === 1)
        const rightCol = existingConfig.value.layout.columns.find(c => c.index === 2)
        fillColumn.value.left = leftCol?.fill ?? false
        fillColumn.value.right = rightCol?.fill ?? false
      }
      // 加载左列宽度
      if (existingConfig.value.layout?.leftColumnWidth) {
        savedLeftColumnWidth.value = existingConfig.value.layout.leftColumnWidth
      }
    }
  } catch (e: any) {
    if (e.response?.status !== 404) {
      console.warn('加载配置失败')
    }
  } finally {
    configLoading.value = false
  }
}

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
    } catch (err) {
      alert('JSON 格式错误')
    }
  }
  reader.readAsText(file)
}

const handleJsonPaste = () => {
  try {
    const json = JSON.parse(exampleJsonText.value)
    exampleData.value = json
    parsedFields.value = extractFieldsWithRules(json, customFieldRules.value)
  } catch (err) {
    alert('JSON 格式错误')
  }
}

const openAddCustomRuleDialog = () => {
  customRuleName.value = ''
  customRuleType.value = 'path'
  customRulePath.value = ''
  customRuleRegex.value = ''
  customRuleRegexSource.value = ''
  customRuleFormVisible.value = true
}

const handleAddCustomRule = () => {
  if (!customRuleName.value) {
    alert('请输入规则名称')
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

  if (exampleData.value) {
    parsedFields.value = extractFieldsWithRules(exampleData.value, customFieldRules.value)
  }

  customRuleFormVisible.value = false
}

const handleRemoveCustomRule = (index: number) => {
  customFieldRules.value.splice(index, 1)
  if (exampleData.value) {
    parsedFields.value = extractFieldsWithRules(exampleData.value, customFieldRules.value)
  }
}

const removeModule = (moduleId: string) => {
  placedModules.value = placedModules.value.filter(m => m.id !== moduleId)
  if (selectedModuleId.value === moduleId) {
    selectedModuleId.value = null
  }
}

const selectModule = (module: ModuleInstance) => {
  selectedModuleId.value = module.id
}

const handleSave = async () => {
  if (placedModules.value.length === 0) {
    alert('请至少添加一个模块')
    return
  }

  try {
    const config: PageConfig = {
      modules: placedModules.value.map(m => ({
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
          { index: 2, width: '60%', label: '右列', fill: fillColumn.value.right }
        ]
      },
      dataSource: {
        exampleJsonText: exampleJsonText.value,
        customFieldRules: customFieldRules.value
      }
    }

    await saveAnnotationPageConfig(projectId.value, config)
    alert('配置已保存')
    router.push(`/projects/${projectId.value}`)
  } catch (err: any) {
    alert(err.response?.data?.detail || '保存失败')
  }
}

const openPreview = () => {
  if (placedModules.value.length === 0) {
    alert('请先添加模块')
    return
  }

  const previewConfig: PageConfig = {
    modules: placedModules.value,
    layout: {
      columnCount: 3,
      columns: [
        { index: 0, width: '15%', label: '侧边栏' },
        { index: 1, width: '25%', label: '左列', fill: fillColumn.value.left },
        { index: 2, width: '60%', label: '右列', fill: fillColumn.value.right }
      ],
      leftColumnWidth: savedLeftColumnWidth.value
    },
    dataSource: {
      exampleJsonText: exampleJsonText.value,
      customFieldRules: customFieldRules.value
    }
  }
  localStorage.setItem('annotation-preview-config', JSON.stringify(previewConfig))
  localStorage.setItem('annotation-preview-data', JSON.stringify(exampleData.value))

  const previewUrl = `/projects/${projectId.value}/preview`
  window.open(previewUrl, '_blank')
}

const toggleFill = (column: 'left' | 'right') => {
  fillColumn.value[column] = !fillColumn.value[column]
}

const prevStep = () => {
  if (currentStep.value > 1) currentStep.value--
}

const nextStep = () => {
  if (currentStep.value < 3) currentStep.value++
}

const leftColumnModules = computed<ModuleInstance[]>({
  get: () => placedModules.value.filter(m => m.col === 1),
  set: (val) => {
    const otherModules = placedModules.value.filter(m => m.col !== 1)
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

const handleModuleAdd = (event: any, colIndex: number) => {
  // clone 模式下，vuedraggable 已经自动克隆了元素到目标数组
  // computed setter 会把克隆的 ModuleDefinition 放入 placedModules
  // 我们需要找到这个克隆对象并转换为正确的 ModuleInstance

  const { newIndex } = event

  // 找到刚刚添加的模块（在 placedModules 的末尾或通过 col 筛选）
  const columnModules = placedModules.value.filter(m => m.col === colIndex)
  const clonedItem = columnModules[columnModules.length - 1]  // 最后一个就是刚添加的

  if (!clonedItem) return

  // 克隆的是 ModuleDefinition，其 id 就是 type
  const moduleType = clonedItem.id
  const moduleDef = getModuleById(moduleType)
  if (!moduleDef) return

  // 找到这个克隆对象在 placedModules 中的索引
  const placedIndex = placedModules.value.findIndex(m => m === clonedItem)
  if (placedIndex === -1) return

  // 创建正确的 ModuleInstance 并替换
  const newModule: ModuleInstance = {
    id: `${moduleType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type: moduleType,
    col: colIndex,
    row: 1,
    width: colIndex === 2 ? '60%' : '30%',
    height: '100%',
    config: moduleDef.defaultConfig ? JSON.parse(JSON.stringify(moduleDef.defaultConfig)) : {}
  }

  // 直接替换
  placedModules.value[placedIndex] = newModule
  selectedModuleId.value = newModule.id
  draggingModule.value = null
}

onMounted(() => {
  loadExistingConfig()
})
</script>

<template>
  <div class="configurator">
    <div class="card">
      <!-- 头部 -->
      <div class="card-header">
        <h2 class="card-title">标注页面配置</h2>
        <button class="btn btn-secondary" @click="router.push(`/projects/${projectId}`)">返回</button>
      </div>

      <!-- 步骤条 -->
      <div class="steps">
        <div class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
          <span class="step-number">1</span>
          <span class="step-label">数据源配置</span>
        </div>
        <div class="step-line" :class="{ active: currentStep > 1 }"></div>
        <div class="step" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
          <span class="step-number">2</span>
          <span class="step-label">模块配置</span>
        </div>
        <div class="step-line" :class="{ active: currentStep > 2 }"></div>
        <div class="step" :class="{ active: currentStep >= 3 }">
          <span class="step-number">3</span>
          <span class="step-label">预览保存</span>
        </div>
      </div>

      <!-- 步骤 1: 数据源配置 -->
      <div v-show="currentStep === 1" class="step-content">
        <h3>上传示例 JSON 数据</h3>
        <p class="help-text">上传一条典型的 JSON 数据，系统将自动提取可用字段</p>

        <div class="upload-section">
          <input type="file" id="json-upload" accept=".json" @change="handleFileUpload" style="display: none" />
          <label for="json-upload" class="btn btn-primary">上传 JSON 文件</label>
        </div>

        <div class="divider">或</div>

        <textarea
          v-model="exampleJsonText"
          class="form-input form-textarea"
          rows="10"
          placeholder="粘贴 JSON 数据..."
        ></textarea>
        <button class="btn btn-primary" @click="handleJsonPaste" style="margin-top: 8px">解析 JSON</button>

        <!-- 字段列表 -->
        <div v-if="parsedFields.length > 0" class="fields-section">
          <h4>提取的字段（{{ parsedFields.length }} 个）</h4>
          <p class="help-text">数组字段可直接选择，子字段（└─开头）供参考结构</p>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>字段路径</th>
                  <th>类型</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="field in parsedFields" :key="field.path" :class="{ 'sub-field': field.preview?.startsWith('└─') }">
                  <td><code>{{ field.path }}</code></td>
                  <td>
                    <span class="tag tag-primary">{{ field.type }}</span>
                  </td>
                  <td>{{ field.preview || (field.sampleValue ? String(field.sampleValue).slice(0, 30) : '-') }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 步骤 2: 模块配置 -->
      <div v-show="currentStep === 2" class="step-content">
        <div class="config-layout">
          <!-- 画布 -->
          <div class="canvas-area">
            <h4>画布预览</h4>
            <p class="help-text">拖拽模块到画布</p>
            <div class="canvas">
              <!-- 侧边栏 -->
              <div class="canvas-col sidebar-col" style="width: 15%; min-width: 180px">
                <div class="column-header">侧边栏 (固定)</div>
                <div class="sidebar-fixed">
                  <div class="module-block sidebar-module">
                    <div class="module-avatar">侧</div>
                    <div class="module-info">
                      <div class="module-name">标注任务列表</div>
                      <div class="module-desc">系统自动添加</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 左列 -->
              <div class="canvas-col left-col">
                <div class="column-header">
                  <span>左列</span>
                  <button
                    class="btn-fill"
                    :class="{ active: fillColumn.left }"
                    @click="toggleFill('left')"
                    :title="fillColumn.left ? '取消平铺' : '平铺满画布'"
                  >
                    {{ fillColumn.left ? '取消平铺' : '平铺' }}
                  </button>
                </div>
                <draggable
                  v-model="leftColumnModules"
                  :group="{ name: 'modules', pull: true, put: true }"
                  :animation="200"
                  item-key="id"
                  class="draggable-list"
                  @add="(e) => handleModuleAdd(e, 1)"
                >
                  <template #item="{ element: module }">
                    <div
                      class="module-block"
                      :class="{ selected: selectedModuleId === module.id }"
                      @click="selectModule(module)"
                    >
                      <div class="module-avatar">{{ getModuleById(module.type)?.icon || '📦' }}</div>
                      <div class="module-info">
                        <div class="module-name">{{ getModuleById(module.type)?.name }}</div>
                      </div>
                      <button class="remove-btn" @click.stop="removeModule(module.id)">×</button>
                    </div>
                  </template>
                  <template #empty>
                    <div class="empty-column">拖拽组件到此处</div>
                  </template>
                </draggable>
              </div>

              <!-- 右列 -->
              <div class="canvas-col right-col">
                <div class="column-header">
                  <span>右列</span>
                  <button
                    class="btn-fill"
                    :class="{ active: fillColumn.right }"
                    @click="toggleFill('right')"
                    :title="fillColumn.right ? '取消平铺' : '平铺满画布'"
                  >
                    {{ fillColumn.right ? '取消平铺' : '平铺' }}
                  </button>
                </div>
                <draggable
                  v-model="rightColumnModules"
                  :group="{ name: 'modules', pull: true, put: true }"
                  :animation="200"
                  item-key="id"
                  class="draggable-list"
                  @add="(e) => handleModuleAdd(e, 2)"
                >
                  <template #item="{ element: module }">
                    <div
                      class="module-block"
                      :class="{ selected: selectedModuleId === module.id }"
                      @click="selectModule(module)"
                    >
                      <div class="module-avatar">{{ getModuleById(module.type)?.icon || '📦' }}</div>
                      <div class="module-info">
                        <div class="module-name">{{ getModuleById(module.type)?.name }}</div>
                      </div>
                      <button class="remove-btn" @click.stop="removeModule(module.id)">×</button>
                    </div>
                  </template>
                  <template #empty>
                    <div class="empty-column">拖拽组件到此处</div>
                  </template>
                </draggable>
              </div>
            </div>
          </div>

          <!-- 属性面板 -->
          <div class="props-panel" v-if="selectedModule">
            <h4>模块配置</h4>
            <ModuleConfigEditor
              :module-type="selectedModule.type"
              :config="selectedModule.config"
              :parsed-fields="parsedFields"
              @update:config="selectedModule.config = $event"
            />
          </div>
          <div v-else class="props-panel empty">
            <p>点击画布中的模块配置参数</p>
          </div>
        </div>

        <!-- 组件市场 -->
        <h3 style="margin-top: 24px">组件市场</h3>
        <p class="help-text">拖拽组件到画布</p>
        <draggable
          :list="marketModules"
          :group="{ name: 'modules', pull: 'clone', put: false }"
          :sort="false"
          :animation="200"
          item-key="id"
          class="component-market"
          @start="handleMarketDragStart"
        >
          <template #item="{ element: module }">
            <div class="component-card">
              <div class="component-avatar">{{ module.icon }}</div>
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
        <pre class="config-preview">{{ JSON.stringify({ modules: placedModules.map(m => ({ id: m.id, type: m.type, config: m.config })) }, null, 2) }}</pre>

        <div class="divider">测试标注页面</div>
        <p class="help-text">在保存前测试标注页面效果</p>
        <button class="btn btn-primary" @click="openPreview">打开测试页面</button>
      </div>

      <!-- 底部按钮 -->
      <div class="card-footer">
        <button class="btn btn-secondary" @click="prevStep" :disabled="currentStep === 1">上一步</button>
        <button v-if="currentStep < 3" class="btn btn-primary" @click="nextStep" :disabled="currentStep === 1 && parsedFields.length === 0">下一步</button>
        <button v-else class="btn btn-primary" @click="handleSave">保存配置</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.configurator {
  padding: 24px;
}

.card {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
  border-radius: 12px 12px 0 0;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.card-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 16px 20px;
  border-top: 1px solid #E5E7EB;
}

/* 步骤条 */
.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #E5E7EB;
  color: #6B7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.2s;
}

.step.active .step-number {
  background: #165DFF;
  color: white;
}

.step.done .step-number {
  background: #10B981;
  color: white;
}

.step-label {
  font-size: 14px;
  color: #6B7280;
}

.step.active .step-label {
  color: #111827;
  font-weight: 500;
}

.step-line {
  width: 60px;
  height: 2px;
  background: #E5E7EB;
  margin: 0 16px;
}

.step-line.active {
  background: #165DFF;
}

.step-content {
  padding: 20px;
  min-height: 400px;
}

.step-content h3 {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

.step-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.help-text {
  color: #6B7280;
  font-size: 13px;
  margin-bottom: 16px;
}

.divider {
  text-align: center;
  color: #9CA3AF;
  margin: 20px 0;
  position: relative;
}

.divider::before,
.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 45%;
  height: 1px;
  background: #E5E7EB;
}

.divider::before { left: 0; }
.divider::after { right: 0; }

.upload-section {
  margin-bottom: 20px;
}

.fields-section {
  margin-top: 24px;
}

.sub-field {
  background: #F9FAFB;
}

.sub-field code {
  color: #6B7280;
  font-size: 12px;
}

.table-container {
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  overflow: hidden;
}

.form-textarea {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.config-layout {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 16px;
}

.canvas-area h4 {
  margin: 0 0 8px 0;
}

.canvas {
  display: flex;
  gap: 8px;
  height: 500px;
  background: #F9FAFB;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
}

.canvas-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.canvas-col.sidebar-col {
  flex: 0 0 auto;
}

.canvas-col.left-col {
  flex: 1;
}

.canvas-col.right-col {
  flex: 2;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #6B7280;
  padding: 4px 8px;
  background: #F3F4F6;
  border-radius: 6px;
}

.btn-fill {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid #D1D5DB;
  border-radius: 4px;
  background: #FFFFFF;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-fill:hover {
  background: #F3F4F6;
  border-color: #9CA3AF;
}

.btn-fill.active {
  background: #165DFF;
  color: white;
  border-color: #165DFF;
}

.draggable-list {
  flex: 1;
  min-height: 100px;
}

.empty-column {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  border: 2px dashed #E5E7EB;
  border-radius: 8px;
  color: #9CA3AF;
  font-size: 13px;
}

.module-block {
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border: 2px solid #E5E7EB;
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  margin-bottom: 8px;
}

.module-block:hover {
  border-color: #165DFF;
}

.module-block.selected {
  border-color: #165DFF;
  background: #E8F3FF;
}

.module-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #165DFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.sidebar-module .module-avatar {
  background: #10B981;
}

.module-info {
  flex: 1;
}

.module-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.module-desc {
  font-size: 12px;
  color: #6B7280;
}

.remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border: none;
  background: #FEE2E2;
  color: #EF4444;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.2s;
}

.module-block:hover .remove-btn {
  opacity: 1;
}

.props-panel {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  height: fit-content;
  max-height: 600px;
  overflow: auto;
}

.props-panel.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9CA3AF;
  min-height: 200px;
}

.props-panel h4 {
  margin: 0;
  padding: 12px 16px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
  position: sticky;
  top: 0;
}

.component-market {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.component-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px;
  cursor: grab;
  transition: all 0.2s;
  min-height: 120px;
}

.component-card:hover {
  border-color: #165DFF;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.15);
}

.component-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #165DFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 12px;
}

.component-info {
  text-align: center;
}

.component-info h4 {
  margin: 0 0 6px 0;
}

.component-desc {
  margin: 0;
  font-size: 12px;
  color: #6B7280;
}

.config-preview {
  background: #F9FAFB;
  padding: 16px;
  border-radius: 12px;
  font-family: monospace;
  font-size: 12px;
  max-height: 400px;
  overflow: auto;
  border: 1px solid #E5E7EB;
}
</style>