<script setup lang="ts">
/**
 * ImageBBoxAnnotator - 图片拉框标注器 v2
 *
 * 功能：
 * - 图片展示 + bbox 框绘制
 * - 拖拽调整 bbox
 * - 新建 bbox
 * - 集成 BboxPropertyEditor
 *
 * 使用共享上下文进行状态管理
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAnnotationContext } from '@/composables/useAnnotationContext'
import BboxPropertyEditor from './BboxPropertyEditor.vue'

// Props
const props = defineProps<{
  title?: string
  readonly?: boolean
  showTitle?: boolean  // 是否显示内部标题
}>()

// 获取上下文
const context = useAnnotationContext()
const {
  bboxList,
  selectedId,
  showAllBboxes,
  selectedBbox,
  representField,
  config,
  updateBboxCoord,
  updateBbox,
  addBbox,
  selectBbox
} = context

// ===== 图片相关 =====
const imageContainer = ref<HTMLElement | null>(null)
const imagePreview = ref<HTMLImageElement | null>(null)
const imageLoaded = ref(false)
const naturalWidth = ref(0)
const naturalHeight = ref(0)

// 图片 URL（处理路径清洗和代理）
const imageUrl = computed(() => {
  if (!config.value) return ''

  let rawValue = context.rawData.value?.[config.value.image.field]

  // 如果是数组，取第一个元素
  if (Array.isArray(rawValue)) {
    rawValue = rawValue[0]
  }

  let url = typeof rawValue === 'string' ? rawValue : ''

  if (!url) return ''

  // 路径清洗
  const pathClean = config.value.image.pathClean
  if (url && pathClean?.enabled && pathClean?.prefix) {
    let prefixes = pathClean.prefix
    if (!Array.isArray(prefixes)) {
      prefixes = [prefixes]
    }
    for (const prefix of prefixes) {
      if (prefix && url.startsWith(prefix)) {
        url = url.replace(prefix, '')
        break
      }
    }
  }

  // 如果配置了图片根目录，使用代理 URL
  if (context.imageBasePath.value && context.projectId.value) {
    return `/api/v1/projects/${context.projectId.value}/images/${encodeURIComponent(url)}`
  }

  return url
})

// 图片加载完成
const onImageLoad = () => {
  if (!imagePreview.value) return
  naturalWidth.value = imagePreview.value.naturalWidth
  naturalHeight.value = imagePreview.value.naturalHeight
  imageLoaded.value = true
}

// ===== 缩放模式 =====
const zoomMode = ref(false)
const zoomLevel = ref(1)
const minZoom = 0.25
const maxZoom = 4
const zoomStep = 0.25

// 拖动画布
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })
const imageTranslate = ref({ x: 0, y: 0 })

const toggleZoomMode = () => {
  zoomMode.value = !zoomMode.value
  if (!zoomMode.value) {
    resetZoom()
  }
}

const zoomIn = () => {
  if (zoomLevel.value < maxZoom) {
    zoomLevel.value = Math.min(maxZoom, zoomLevel.value + zoomStep)
  }
}

const zoomOut = () => {
  if (zoomLevel.value > minZoom) {
    zoomLevel.value = Math.max(minZoom, zoomLevel.value - zoomStep)
  }
}

const resetZoom = () => {
  zoomLevel.value = 1
  imageTranslate.value = { x: 0, y: 0 }
}

// 滚轮缩放（仅在缩放模式下生效）
const handleWheel = (e: WheelEvent) => {
  if (!zoomMode.value) return
  e.preventDefault()
  if (e.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

// 拖动画布（缩放模式下）
const handleCanvasMouseDown = (e: MouseEvent) => {
  if (!zoomMode.value || e.button !== 0) return
  if (!imageContainer.value) return

  isPanning.value = true
  panStart.value = {
    x: e.clientX - imageTranslate.value.x,
    y: e.clientY - imageTranslate.value.y
  }

  document.addEventListener('mousemove', handleCanvasMouseMove)
  document.addEventListener('mouseup', handleCanvasMouseUp)
  e.preventDefault()
}

const handleCanvasMouseMove = (e: MouseEvent) => {
  if (!isPanning.value) return

  imageTranslate.value = {
    x: e.clientX - panStart.value.x,
    y: e.clientY - panStart.value.y
  }
}

const handleCanvasMouseUp = () => {
  isPanning.value = false
  document.removeEventListener('mousemove', handleCanvasMouseMove)
  document.removeEventListener('mouseup', handleCanvasMouseUp)
}

// 计算 bbox 显示样式（应用缩放和平移）
const getBboxStyle = (bbox: [number, number, number, number]) => {
  return {
    left: bbox[0] * zoomLevel.value + imageTranslate.value.x + 'px',
    top: bbox[1] * zoomLevel.value + imageTranslate.value.y + 'px',
    width: (bbox[2] - bbox[0]) * zoomLevel.value + 'px',
    height: (bbox[3] - bbox[1]) * zoomLevel.value + 'px'
  }
}

// ===== BBox 可见性 =====
const isBboxVisible = (id: string): boolean => {
  if (showAllBboxes.value) return true
  if (!selectedId.value) return false
  return id === selectedId.value
}

const isSelected = (id: string): boolean => {
  return id === selectedId.value
}

// ===== 获取当前显示缩放比例 =====
const getCurrentScale = () => {
  // 返回显示缩放比例（zoomLevel）
  return {
    scaleX: zoomLevel.value,
    scaleY: zoomLevel.value
  }
}

// ===== 拖拽调整 =====
const isDragging = ref(false)
const isResizing = ref(false)
const resizeHandle = ref<string | null>(null)
const dragStart = ref({ x: 0, y: 0 })
const bboxStart = ref({ left: 0, top: 0, width: 0, height: 0 })
const currentDragId = ref<string | null>(null)

// 点击 bbox
const handleBboxClick = (id: string, event: MouseEvent) => {
  if (props.readonly) return
  event.stopPropagation()
  selectBbox(id)
}

// 开始拖拽
const handleBboxMouseDown = (e: MouseEvent, id: string) => {
  if (props.readonly || e.button !== 0) return

  const target = e.target as HTMLElement
  const handle = target.closest('.resize-handle') as HTMLElement | null

  if (handle) {
    isResizing.value = true
    resizeHandle.value = handle.dataset.handle || null
  } else {
    isDragging.value = true
  }

  currentDragId.value = id
  selectBbox(id)

  e.preventDefault()
  e.stopPropagation()

  const { scaleX, scaleY } = getCurrentScale()
  const bbox = bboxList.value.find(b => b.id === id)
  if (!bbox) return

  dragStart.value = { x: e.clientX, y: e.clientY }
  bboxStart.value = {
    left: bbox.bbox[0],
    top: bbox.bbox[1],
    width: bbox.bbox[2] - bbox.bbox[0],
    height: bbox.bbox[3] - bbox.bbox[1]
  }

  document.addEventListener('mousemove', handleBboxMousemove)
  document.addEventListener('mouseup', handleBboxMouseup)
}

// 拖拽中
const handleBboxMousemove = (e: MouseEvent) => {
  if (!currentDragId.value || (!isDragging.value && !isResizing.value)) return

  const { scaleX, scaleY } = getCurrentScale()
  const dx = (e.clientX - dragStart.value.x) / scaleX
  const dy = (e.clientY - dragStart.value.y) / scaleY

  let newBbox: [number, number, number, number]

  if (isDragging.value) {
    newBbox = [
      Math.max(0, Math.round(bboxStart.value.left + dx)),
      Math.max(0, Math.round(bboxStart.value.top + dy)),
      Math.min(naturalWidth.value, Math.round(bboxStart.value.left + bboxStart.value.width + dx)),
      Math.min(naturalHeight.value, Math.round(bboxStart.value.top + bboxStart.value.height + dy))
    ]
  } else if (isResizing.value && resizeHandle.value) {
    let { left, top, width, height } = bboxStart.value

    switch (resizeHandle.value) {
      case 'nw':
        left = Math.max(0, left + dx)
        top = Math.max(0, top + dy)
        width = width - dx
        height = height - dy
        break
      case 'n':
        top = Math.max(0, top + dy)
        height = height - dy
        break
      case 'ne':
        top = Math.max(0, top + dy)
        width = Math.max(10, width + dx)
        height = height - dy
        break
      case 'e':
        width = Math.max(10, width + dx)
        break
      case 'se':
        width = Math.max(10, width + dx)
        height = Math.max(10, height + dy)
        break
      case 's':
        height = Math.max(10, height + dy)
        break
      case 'sw':
        left = Math.max(0, left + dx)
        width = Math.max(10, width - dx)
        height = Math.max(10, height + dy)
        break
      case 'w':
        left = Math.max(0, left + dx)
        width = Math.max(10, width - dx)
        break
    }

    newBbox = [
      Math.round(left),
      Math.round(top),
      Math.round(left + width),
      Math.round(top + height)
    ]
  } else {
    return
  }

  updateBboxCoord(currentDragId.value, newBbox)
}

// 拖拽结束
const handleBboxMouseup = () => {
  isDragging.value = false
  isResizing.value = false
  resizeHandle.value = null
  currentDragId.value = null

  document.removeEventListener('mousemove', handleBboxMousemove)
  document.removeEventListener('mouseup', handleBboxMouseup)
}

// 右键新建 bbox
const handleCanvasContextMenu = (e: MouseEvent) => {
  if (props.readonly) return

  e.preventDefault()

  if (!imagePreview.value) return

  const rect = imagePreview.value.getBoundingClientRect()
  // 计算点击位置对应的原始图片坐标
  const x = Math.round((e.clientX - rect.left) / zoomLevel.value)
  const y = Math.round((e.clientY - rect.top) / zoomLevel.value)

  addBbox([x - 50, y - 25, x + 50, y + 25])
}

// ===== 键盘操作 =====
const handleKeyDown = (e: KeyboardEvent) => {
  if (!selectedId.value || props.readonly) return

  const bbox = bboxList.value.find(b => b.id === selectedId.value)
  if (!bbox) return

  const step = e.shiftKey ? 10 : 1
  const [x1, y1, x2, y2] = bbox.bbox

  switch (e.key) {
    case 'ArrowUp':
      e.preventDefault()
      updateBboxCoord(selectedId.value, [x1, y1 - step, x2, y2 - step])
      break
    case 'ArrowDown':
      e.preventDefault()
      updateBboxCoord(selectedId.value, [x1, y1 + step, x2, y2 + step])
      break
    case 'ArrowLeft':
      e.preventDefault()
      updateBboxCoord(selectedId.value, [x1 - step, y1, x2 - step, y2])
      break
    case 'ArrowRight':
      e.preventDefault()
      updateBboxCoord(selectedId.value, [x1 + step, y1, x2 + step, y2])
      break
  }
}

// 切换显示全部
const toggleShowAll = () => {
  showAllBboxes.value = !showAllBboxes.value
}

// ===== 属性编辑相关 =====
const hasSelection = computed(() => selectedBbox.value !== null)

const properties = computed(() => config.value?.bboxProperties || [])

const getPropertyValue = (name: string) => {
  return selectedBbox.value?.[name]
}

const setProperty = (name: string, value: any) => {
  if (selectedId.value) {
    updateBbox(selectedId.value, name, value)
  }
}

// 当前 bbox 坐标
const currentBbox = computed({
  get: () => selectedBbox.value?.bbox || [0, 0, 0, 0],
  set: (val) => {
    if (selectedId.value) {
      updateBboxCoord(selectedId.value, val as [number, number, number, number])
    }
  }
})

const x1 = computed({
  get: () => currentBbox.value[0],
  set: (val) => { currentBbox.value = [val, currentBbox.value[1], currentBbox.value[2], currentBbox.value[3]] }
})
const y1 = computed({
  get: () => currentBbox.value[1],
  set: (val) => { currentBbox.value = [currentBbox.value[0], val, currentBbox.value[2], currentBbox.value[3]] }
})
const x2 = computed({
  get: () => currentBbox.value[2],
  set: (val) => { currentBbox.value = [currentBbox.value[0], currentBbox.value[1], val, currentBbox.value[3]] }
})
const y2 = computed({
  get: () => currentBbox.value[3],
  set: (val) => { currentBbox.value = [currentBbox.value[0], currentBbox.value[1], currentBbox.value[2], val] }
})

// ===== 面板宽度调整 =====
// 外层：图片区域 vs 右侧面板组
const imagePanelWidth = ref(60) // 百分比
const isResizingOuter = ref(false)
const resizeOuterStartX = ref(0)
const resizeOuterStartWidth = ref(0)

// 内层：框调整 vs 信息调整
const bboxPanelWidth = ref(50) // 百分比（相对于右侧面板组）
const isResizingInner = ref(false)
const resizeInnerStartX = ref(0)
const resizeInnerStartWidth = ref(0)

// 外层调整
const startResizeOuter = (event: MouseEvent) => {
  if (props.readonly) return

  isResizingOuter.value = true
  resizeOuterStartX.value = event.clientX
  resizeOuterStartWidth.value = imagePanelWidth.value

  document.addEventListener('mousemove', handleResizeOuter)
  document.addEventListener('mouseup', stopResizeOuter)
  event.preventDefault()
}

const handleResizeOuter = (event: MouseEvent) => {
  if (!isResizingOuter.value) return

  const container = document.querySelector('.annotator-body')
  if (!container) return

  const containerWidth = container.getBoundingClientRect().width
  const deltaX = event.clientX - resizeOuterStartX.value
  const deltaPercent = (deltaX / containerWidth) * 100

  imagePanelWidth.value = Math.max(30, Math.min(70, resizeOuterStartWidth.value + deltaPercent))
}

const stopResizeOuter = () => {
  isResizingOuter.value = false
  document.removeEventListener('mousemove', handleResizeOuter)
  document.removeEventListener('mouseup', stopResizeOuter)
}

// 内层调整
const startResizeInner = (event: MouseEvent) => {
  if (props.readonly) return

  isResizingInner.value = true
  resizeInnerStartX.value = event.clientX
  resizeInnerStartWidth.value = bboxPanelWidth.value

  document.addEventListener('mousemove', handleResizeInner)
  document.addEventListener('mouseup', stopResizeInner)
  event.preventDefault()
}

const handleResizeInner = (event: MouseEvent) => {
  if (!isResizingInner.value) return

  const container = document.querySelector('.right-panel-group')
  if (!container) return

  const containerWidth = container.getBoundingClientRect().width
  const deltaX = event.clientX - resizeInnerStartX.value // 向右拖动增大框面板宽度
  const deltaPercent = (deltaX / containerWidth) * 100

  bboxPanelWidth.value = Math.max(30, Math.min(70, resizeInnerStartWidth.value + deltaPercent))
}

const stopResizeInner = () => {
  isResizingInner.value = false
  document.removeEventListener('mousemove', handleResizeInner)
  document.removeEventListener('mouseup', stopResizeInner)
}

// ===== 生命周期 =====
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('mousemove', handleBboxMousemove)
  document.removeEventListener('mouseup', handleBboxMouseup)
  document.removeEventListener('mousemove', handleResizeOuter)
  document.removeEventListener('mouseup', stopResizeOuter)
  document.removeEventListener('mousemove', handleResizeInner)
  document.removeEventListener('mouseup', stopResizeInner)
})

// 监听图片变化重置缩放
watch(imageUrl, () => {
  resetZoom()
  imageLoaded.value = false
})
</script>

<template>
  <div class="image-bbox-annotator">
    <!-- 工具栏 -->
    <div class="annotator-header">
      <div class="header-left">
        <span v-if="showTitle" class="annotator-title">{{ title || config?.title || '图片标注器' }}</span>
        <button
          class="btn-text"
          :class="{ active: showAllBboxes }"
          @click="toggleShowAll"
        >
          显示全部
        </button>
        <button
          class="btn-text"
          :class="{ active: zoomMode }"
          @click="toggleZoomMode"
        >
          缩放
        </button>
      </div>
      <div class="header-right">
        <template v-if="zoomMode">
          <button class="btn-sm" @click="zoomOut" :disabled="zoomLevel <= minZoom" title="缩小">
            −
          </button>
          <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
          <button class="btn-sm" @click="zoomIn" :disabled="zoomLevel >= maxZoom" title="放大">
            +
          </button>
          <button class="btn-sm" @click="resetZoom" title="重置">
            重置
          </button>
        </template>
      </div>
    </div>

    <!-- 主内容区：左侧图片 + 右侧面板组 -->
    <div class="annotator-body">
      <!-- 左侧：图片画布 -->
      <div
        ref="imageContainer"
        class="image-canvas-wrapper"
        :class="{ 'zoom-mode': zoomMode, 'panning': isPanning }"
        :style="{ width: imagePanelWidth + '%' }"
        @wheel="handleWheel"
        @mousedown="handleCanvasMouseDown"
        @contextmenu="handleCanvasContextMenu"
      >
        <div class="image-canvas" :class="{ loaded: imageLoaded }">
          <img
            ref="imagePreview"
            :src="imageUrl"
            alt="标注图片"
            class="image-element"
            :style="{ transform: `translate(${imageTranslate.x}px, ${imageTranslate.y}px) scale(${zoomLevel})` }"
            @load="onImageLoad"
          />

          <!-- BBox 覆盖层 -->
          <div v-if="imageLoaded" class="bbox-overlays">
            <div
              v-for="bbox in bboxList"
              :key="bbox.id"
              class="bbox-overlay"
              :class="{
                visible: isBboxVisible(bbox.id),
                selected: isSelected(bbox.id)
              }"
              :style="getBboxStyle(bbox.bbox)"
              @mousedown="handleBboxMouseDown($event, bbox.id)"
              @click="handleBboxClick(bbox.id, $event)"
            >
              <!-- 代表属性标签 -->
              <span
                v-if="isSelected(bbox.id) && bbox[representField]"
                class="bbox-label"
              >
                {{ bbox[representField] }}
              </span>

              <!-- 8 点调整手柄 -->
              <template v-if="isSelected(bbox.id)">
                <div
                  v-for="handle in ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w']"
                  :key="handle"
                  class="resize-handle"
                  :class="handle"
                  :data-handle="handle"
                ></div>
              </template>
            </div>
          </div>
        </div>

        <!-- 加载提示 -->
        <div v-if="!imageLoaded" class="image-loading">
          加载中...
        </div>
      </div>

      <!-- 外层调整手柄（图片 | 右侧面板组） -->
      <div
        v-if="!readonly"
        class="outer-resize-handle"
        :class="{ active: isResizingOuter }"
        @mousedown="startResizeOuter"
      >
        <div class="resize-bar"></div>
      </div>

      <!-- 右侧面板组：框调整 + 信息调整 -->
      <div
        class="right-panel-group"
        :style="{ width: (100 - imagePanelWidth) + '%' }"
      >
        <!-- 左侧：框调整（BboxPropertyEditor） -->
        <div
          class="bbox-panel"
          :style="{ width: bboxPanelWidth + '%' }"
        >
          <BboxPropertyEditor :readonly="readonly" />
        </div>

        <!-- 内层调整手柄（框调整 | 信息调整） -->
        <div
          v-if="!readonly"
          class="inner-resize-handle"
          :class="{ active: isResizingInner }"
          @mousedown="startResizeInner"
        >
          <div class="resize-bar"></div>
        </div>

        <!-- 右侧：信息调整（属性编辑） -->
        <div
          class="info-panel"
          :style="{ width: (100 - bboxPanelWidth) + '%' }"
        >
          <!-- 无选中提示 -->
          <div v-if="!hasSelection" class="no-selection">
            <p>请选择一个框</p>
          </div>

          <!-- 编辑表单 -->
          <template v-else>
            <div class="panel-section">
              <div class="panel-section-title">坐标</div>
              <div class="coord-grid">
                <div class="coord-item">
                  <label>X1</label>
                  <input type="number" v-model.number="x1" :disabled="readonly" />
                </div>
                <div class="coord-item">
                  <label>Y1</label>
                  <input type="number" v-model.number="y1" :disabled="readonly" />
                </div>
                <div class="coord-item">
                  <label>X2</label>
                  <input type="number" v-model.number="x2" :disabled="readonly" />
                </div>
                <div class="coord-item">
                  <label>Y2</label>
                  <input type="number" v-model.number="y2" :disabled="readonly" />
                </div>
              </div>
              <div class="coord-size">
                {{ Math.abs(x2 - x1) }} × {{ Math.abs(y2 - y1) }} px
              </div>
            </div>

            <!-- 动态属性 -->
            <div v-if="properties.length > 0" class="panel-section">
              <div class="panel-section-title">属性</div>
              <div class="property-list">
                <div
                  v-for="prop in properties"
                  :key="prop.name"
                  class="property-item"
                >
                  <label>{{ prop.displayName }}</label>
                  <input
                    type="text"
                    :value="getPropertyValue(prop.name)"
                    @input="setProperty(prop.name, ($event.target as HTMLInputElement).value)"
                    :disabled="readonly"
                    :placeholder="String(prop.defaultValue || '')"
                  />
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.image-bbox-annotator {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 300px;  /* 最小高度 */
  background: #FFFFFF;
  border-radius: 12px;
  overflow: hidden;
}

.annotator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.annotator-title {
  font-weight: 600;
  font-size: 13px;
  color: #111827;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  border: none;
  border-radius: 8px;
  background: #FFFFFF;
  color: #111827;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #F3F4F6;
  }

  &.active {
    background: #165DFF;
    color: white;
  }
}

.btn-text {
  padding: 4px 12px;
  font-size: 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    color: #165DFF;
    background: #F3F4F6;
  }

  &.active {
    color: #165DFF;
    background: #E8F3FF;
  }
}

.annotator-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.image-canvas-wrapper {
  overflow: auto;
  padding: 16px;
  background: #F9FAFB;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  position: relative;
  flex-shrink: 0;

  &.zoom-mode {
    cursor: grab;
  }

  &.zoom-mode.panning {
    cursor: grabbing;
  }
}

.image-canvas {
  position: relative;
  display: inline-block;
}

.image-element {
  display: block;
  border-radius: 8px;
  max-width: none;
  height: auto;
  transform-origin: top left;
}

.bbox-overlays {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.bbox-overlay {
  position: absolute;
  border: 2px solid #165DFF;
  background-color: rgba(22, 93, 255, 0.15);
  box-sizing: border-box;
  pointer-events: auto;
  cursor: pointer;
  display: none;

  &.visible {
    display: block;
  }

  &.selected {
    background-color: rgba(22, 93, 255, 0.25);
    border-width: 2px;
  }

  &:hover {
    background-color: rgba(22, 93, 255, 0.3);
  }
}

.bbox-label {
  position: absolute;
  top: -22px;
  left: 0;
  background: #165DFF;
  color: white;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
}

.resize-handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #165DFF;
  border: 2px solid white;
  border-radius: 50%;
  z-index: 10;

  &.nw { left: -5px; top: -5px; cursor: nw-resize; }
  &.n { left: 50%; top: -5px; cursor: n-resize; transform: translateX(-50%); }
  &.ne { right: -5px; top: -5px; cursor: ne-resize; }
  &.e { right: -5px; top: 50%; cursor: e-resize; transform: translateY(-50%); }
  &.se { right: -5px; bottom: -5px; cursor: se-resize; }
  &.s { left: 50%; bottom: -5px; cursor: s-resize; transform: translateX(-50%); }
  &.sw { left: -5px; bottom: -5px; cursor: sw-resize; }
  &.w { left: -5px; top: 50%; cursor: w-resize; transform: translateY(-50%); }
}

.image-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #9CA3AF;
  font-size: 14px;
}

/* 外层调整手柄 */
.outer-resize-handle {
  width: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: col-resize;
  background: #FFFFFF;
  border-left: 1px solid #E5E7EB;
  border-right: 1px solid #E5E7EB;
  transition: background 0.15s ease;
  z-index: 10;

  &:hover {
    background: #E8F3FF;
  }

  &.active {
    background: #E8F3FF;
  }
}

/* 内层调整手柄 */
.inner-resize-handle {
  width: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: col-resize;
  background: #FFFFFF;
  border-left: 1px solid #E5E7EB;
  border-right: 1px solid #E5E7EB;
  transition: background 0.15s ease;
  z-index: 10;

  &:hover {
    background: #E8F3FF;
  }

  &.active {
    background: #E8F3FF;
  }
}

.resize-bar {
  width: 4px;
  height: 40px;
  border-radius: 2px;
  background: #E5E7EB;
  transition: background 0.15s ease;

  .outer-resize-handle:hover &,
  .outer-resize-handle.active &,
  .inner-resize-handle:hover &,
  .inner-resize-handle.active & {
    background: #165DFF;
  }
}

/* 右侧面板组 */
.right-panel-group {
  display: flex;
  flex-shrink: 0;
  background: #FFFFFF;
}

.bbox-panel {
  flex-shrink: 0;
  border-right: 1px solid #E5E7EB;
}

.info-panel {
  flex-shrink: 0;
  overflow: auto;
  padding: 16px;
  box-sizing: border-box;
}

.no-selection {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9CA3AF;
  font-size: 13px;
}

.panel-section {
  margin-bottom: 20px;
  padding-right: 12px;
}

.panel-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.coord-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.coord-item {
  display: flex;
  flex-direction: column;
  gap: 4px;

  label {
    font-size: 12px;
    color: #6B7280;
  }

  input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
    transition: border-color 0.15s;
    box-sizing: border-box;

    &:focus {
      border-color: #165DFF;
    }

    &:disabled {
      background: #F9FAFB;
    }
  }
}

.coord-size {
  margin-top: 10px;
  font-size: 12px;
  color: #9CA3AF;
}

.property-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.property-item {
  display: flex;
  flex-direction: column;
  gap: 4px;

  label {
    font-size: 12px;
    color: #6B7280;
  }

  input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
    transition: border-color 0.15s;
    box-sizing: border-box;

    &:focus {
      border-color: #165DFF;
    }
  }
}

.zoom-level {
  font-size: 12px;
  color: #374151;
  min-width: 45px;
  text-align: center;
}
</style>