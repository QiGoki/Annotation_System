<script setup lang="ts">
/**
 * 图片拉框标注器组件
 * 支持功能：
 * - 图片显示与缩放/平移
 * - 拖拽绘制 bbox
 * - 8 点调整 bbox 大小
 * - 键盘方向键微调
 * - Bbox 显示/隐藏切换
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

export interface BboxData {
  path: number[]        // 组件在树中的路径
  bbox: [number, number, number, number]  // [x1, y1, x2, y2]
  type?: string
  text?: string
}

export interface ImageBBoxAnnotatorProps {
  imageUrl: string
  bboxes: BboxData[]
  selectedBboxPath?: number[] | null
  showAllBboxes?: boolean
  zoomable?: boolean
  bboxEditable?: boolean
}

const props = withDefaults(defineProps<ImageBBoxAnnotatorProps>(), {
  selectedBboxPath: null,
  showAllBboxes: false,
  zoomable: true,
  bboxEditable: true
})

const emit = defineEmits<{
  'update:selectedBboxPath': [path: number[] | null]
  'update:bbox': [path: number[], bbox: [number, number, number, number]]
  'bbox:select': [path: number[]]
  'image:load': [width: number, height: number]
}>()

// DOM 引用
const imageContainer = ref<HTMLElement | null>(null)
const imageCanvas = ref<HTMLElement | null>(null)
const imagePreview = ref<HTMLImageElement | null>(null)
const bboxOverlays = ref<HTMLElement | null>(null)

// 图片状态
const imageLoaded = ref(false)
const naturalWidth = ref(0)
const naturalHeight = ref(0)

// 缩放状态
const zoomMode = ref(false)
const zoomLevel = ref(1)
const imageTranslate = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })

// 拖拽/调整状态
const isDragging = ref(false)
const isResizing = ref(false)
const resizeHandle = ref<string | null>(null)
const dragStart = ref({ x: 0, y: 0 })
const bboxStart = ref({ left: 0, top: 0, width: 0, height: 0 })
const currentBboxPath = ref<number[] | null>(null)
const hasDragStarted = ref(false)

// 获取当前缩放比例
const getCurrentScale = () => {
  if (!imagePreview.value) return { scaleX: 1, scaleY: 1 }
  const rect = imagePreview.value.getBoundingClientRect()
  return {
    scaleX: rect.width / naturalWidth.value,
    scaleY: rect.height / naturalHeight.value
  }
}

// 更新图片变换
const updateZoomTransform = () => {
  if (!imageCanvas.value) return
  imageCanvas.value.style.transform = `translate(${imageTranslate.value.x}px, ${imageTranslate.value.y}px) scale(${zoomLevel.value})`
}

// 重置缩放
const resetZoom = () => {
  zoomLevel.value = 1
  imageTranslate.value = { x: 0, y: 0 }
  updateZoomTransform()
}

// 切换放大模式
const toggleZoomMode = () => {
  zoomMode.value = !zoomMode.value
  if (!zoomMode.value) {
    resetZoom()
  }
}

// 图片加载完成
const onImageLoad = () => {
  if (!imagePreview.value) return
  naturalWidth.value = imagePreview.value.naturalWidth
  naturalHeight.value = imagePreview.value.naturalHeight
  imageLoaded.value = true
  emit('image:load', naturalWidth.value, naturalHeight.value)
}

// 监听外部缩放重置
watch(() => props.imageUrl, () => {
  resetZoom()
  imageLoaded.value = false
})

// ========== Bbox 选择 ==========
const selectBbox = (path: number[], event?: MouseEvent) => {
  emit('update:selectedBboxPath', path)
  emit('bbox:select', path)
}

// ========== 拖拽绘制和 8 点调整 ==========
const handleBboxMouseDown = (e: MouseEvent, path: number[]) => {
  if (!props.bboxEditable || e.button !== 0) return

  const target = e.target as HTMLElement
  const handle = target.closest('.resize-handle') as HTMLElement | null

  if (handle) {
    // 调整大小
    isResizing.value = true
    resizeHandle.value = handle.dataset.handle || null
    currentBboxPath.value = path
  } else {
    // 拖动整个框
    isDragging.value = true
    currentBboxPath.value = path
    selectBbox(path, e)
  }

  e.preventDefault()
  e.stopPropagation()

  const { scaleX, scaleY } = getCurrentScale()
  const overlay = target.closest('.bbox-overlay') as HTMLElement

  dragStart.value = { x: e.clientX, y: e.clientY }
  bboxStart.value = {
    left: parseFloat(overlay.style.left),
    top: parseFloat(overlay.style.top),
    width: parseFloat(overlay.style.width),
    height: parseFloat(overlay.style.height)
  }
  hasDragStarted.value = false

  document.addEventListener('mousemove', handleBboxMousemove)
  document.addEventListener('mouseup', handleBboxMouseup)
}

const handleBboxMousemove = (e: MouseEvent) => {
  if ((!isResizing.value && !isDragging.value) || !currentBboxPath.value) return

  const dx = e.clientX - dragStart.value.x
  const dy = e.clientY - dragStart.value.y
  const movedThreshold = 3

  if (!hasDragStarted.value) {
    if (Math.sqrt(dx * dx + dy * dy) < movedThreshold) return
    hasDragStarted.value = true
  }

  e.preventDefault()

  const imgBounds = { maxX: naturalWidth.value, maxY: naturalHeight.value }
  const { scaleX, scaleY } = getCurrentScale()
  const moveDx = dx / scaleX
  const moveDy = dy / scaleY

  if (isDragging.value) {
    // 整体拖动
    let newLeft = Math.max(0, Math.min(bboxStart.value.left + moveDx, imgBounds.maxX - bboxStart.value.width))
    let newTop = Math.max(0, Math.min(bboxStart.value.top + moveDy, imgBounds.maxY - bboxStart.value.height))

    updateBboxPosition(currentBboxPath.value, newLeft, newTop)
  } else if (isResizing.value && resizeHandle.value) {
    // 8 点调整
    const deltaXPx = dx / scaleX
    const deltaYPx = dy / scaleY
    let newLeft = bboxStart.value.left
    let newTop = bboxStart.value.top
    let newWidth = bboxStart.value.width
    let newHeight = bboxStart.value.height

    switch (resizeHandle.value) {
      case 'nw':
        newLeft = Math.max(0, Math.min(bboxStart.value.left + deltaXPx, bboxStart.value.left + bboxStart.value.width - 10))
        newTop = Math.max(0, Math.min(bboxStart.value.top + deltaYPx, bboxStart.value.top + bboxStart.value.height - 10))
        newWidth = bboxStart.value.width - (newLeft - bboxStart.value.left)
        newHeight = bboxStart.value.height - (newTop - bboxStart.value.top)
        break
      case 'n':
        newTop = Math.max(0, Math.min(bboxStart.value.top + deltaYPx, bboxStart.value.top + bboxStart.value.height - 10))
        newHeight = bboxStart.value.height - (newTop - bboxStart.value.top)
        break
      case 'ne':
        newTop = Math.max(0, Math.min(bboxStart.value.top + deltaYPx, bboxStart.value.top + bboxStart.value.height - 10))
        newWidth = Math.max(10, Math.min(bboxStart.value.width + deltaXPx, imgBounds.maxX - bboxStart.value.left))
        newHeight = bboxStart.value.height - (newTop - bboxStart.value.top)
        break
      case 'e':
        newWidth = Math.max(10, Math.min(bboxStart.value.width + deltaXPx, imgBounds.maxX - bboxStart.value.left))
        break
      case 'se':
        newWidth = Math.max(10, Math.min(bboxStart.value.width + deltaXPx, imgBounds.maxX - bboxStart.value.left))
        newHeight = Math.max(10, Math.min(bboxStart.value.height + deltaYPx, imgBounds.maxY - bboxStart.value.top))
        break
      case 's':
        newHeight = Math.max(10, Math.min(bboxStart.value.height + deltaYPx, imgBounds.maxY - bboxStart.value.top))
        break
      case 'sw':
        newLeft = Math.max(0, Math.min(bboxStart.value.left + deltaXPx, bboxStart.value.left + bboxStart.value.width - 10))
        newWidth = bboxStart.value.width - (newLeft - bboxStart.value.left)
        newHeight = Math.max(10, Math.min(bboxStart.value.height + deltaYPx, imgBounds.maxY - bboxStart.value.top))
        break
      case 'w':
        newLeft = Math.max(0, Math.min(bboxStart.value.left + deltaXPx, bboxStart.value.left + bboxStart.value.width - 10))
        newWidth = bboxStart.value.width - (newLeft - bboxStart.value.left)
        break
    }

    updateBboxDimensions(currentBboxPath.value, newLeft, newTop, newWidth, newHeight)
  }
}

const handleBboxMouseup = () => {
  if ((isResizing.value || isDragging.value) && currentBboxPath.value) {
    // 最终保存 bbox 变更由父组件处理
  }

  isResizing.value = false
  isDragging.value = false
  resizeHandle.value = null
  currentBboxPath.value = null
  hasDragStarted.value = false

  document.removeEventListener('mousemove', handleBboxMousemove)
  document.removeEventListener('mouseup', handleBboxMouseup)
}

// 更新 bbox 位置（拖动）
const updateBboxPosition = (path: number[], left: number, top: number) => {
  const bbox = props.bboxes.find(b => getPathKey(b.path) === getPathKey(path))
  if (!bbox) return

  const x1 = Math.round(left)
  const y1 = Math.round(top)
  const x2 = Math.round(left + parseFloat((document.querySelector(`.bbox-overlay[data-path='${JSON.stringify(path)}']`) as HTMLElement)?.style.width || bbox.bbox[2] - bbox.bbox[0]))
  const y2 = Math.round(top + parseFloat((document.querySelector(`.bbox-overlay[data-path='${JSON.stringify(path)}']`) as HTMLElement)?.style.height || bbox.bbox[3] - bbox.bbox[1]))

  emit('update:bbox', path, [x1, y1, x2, y2])
}

// 更新 bbox 尺寸（调整）
const updateBboxDimensions = (path: number[], left: number, top: number, width: number, height: number) => {
  const x1 = Math.round(left)
  const y1 = Math.round(top)
  const x2 = Math.round(left + width)
  const y2 = Math.round(top + height)

  emit('update:bbox', path, [x1, y1, x2, y2])
}

// ========== 键盘微调 ==========
const handleKeyDown = (e: KeyboardEvent) => {
  if (!props.selectedBboxPath || !props.bboxEditable) return

  const bbox = props.bboxes.find(b => getPathKey(b.path) === getPathKey(props.selectedBboxPath!))
  if (!bbox) return

  const step = e.shiftKey ? 10 : 1
  const [x1, y1, x2, y2] = bbox.bbox

  switch (e.key) {
    case 'ArrowUp':
      e.preventDefault()
      emit('update:bbox', props.selectedBboxPath, [x1, y1 - step, x2, y2 - step])
      break
    case 'ArrowDown':
      e.preventDefault()
      emit('update:bbox', props.selectedBboxPath, [x1, y1 + step, x2, y2 + step])
      break
    case 'ArrowLeft':
      e.preventDefault()
      emit('update:bbox', props.selectedBboxPath, [x1 - step, y1, x2 - step, y2])
      break
    case 'ArrowRight':
      e.preventDefault()
      emit('update:bbox', props.selectedBboxPath, [x1 + step, y1, x2 + step, y2])
      break
  }
}

// ========== 工具函数 ==========
const getPathKey = (path: number[]): string => path.join('-')

const isBboxVisible = (path: number[]): boolean => {
  if (props.showAllBboxes) return true
  if (!props.selectedBboxPath) return false
  return getPathKey(path) === getPathKey(props.selectedBboxPath)
}

const isSelectedBbox = (path: number[]): boolean => {
  if (!props.selectedBboxPath) return false
  return getPathKey(path) === getPathKey(props.selectedBboxPath)
}

// ========== 生命周期 ==========
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('mousemove', handleBboxMousemove)
  document.removeEventListener('mouseup', handleBboxMouseup)
})

// ========== 画布拖拽（放大模式下） ==========
const handleCanvasMouseDown = (e: MouseEvent) => {
  if (!zoomMode.value || e.button !== 0) return
  isPanning.value = true
  panStart.value = { x: e.clientX - imageTranslate.value.x, y: e.clientY - imageTranslate.value.y }
  document.addEventListener('mousemove', handleCanvasMousemove)
  document.addEventListener('mouseup', handleCanvasMouseup)
}

const handleCanvasMousemove = (e: MouseEvent) => {
  if (!isPanning.value) return
  e.preventDefault()
  imageTranslate.value = {
    x: e.clientX - panStart.value.x,
    y: e.clientY - panStart.value.y
  }
  updateZoomTransform()
}

const handleCanvasMouseup = () => {
  isPanning.value = false
  document.removeEventListener('mousemove', handleCanvasMousemove)
  document.removeEventListener('mouseup', handleCanvasMouseup)
}
</script>

<template>
  <div class="image-bbox-annotator" :class="{ 'zoom-mode': zoomMode }">
    <!-- 图片信息栏 -->
    <div class="image-info-bar">
      <span class="image-path">{{ imageUrl.split('/').pop() || '-' }}</span>
      <span class="image-dims" v-if="imageLoaded">{{ naturalWidth }} x {{ naturalHeight }}</span>
      <div class="image-actions">
        <button
          v-if="zoomable"
          class="btn-sm"
          :class="{ active: zoomMode }"
          @click="toggleZoomMode"
          title="打开放大模式（z）"
        >
          🔍
        </button>
        <button class="btn-sm" @click="resetZoom" title="重置缩放">100%</button>
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- 图片容器 -->
    <div class="image-wrapper">
      <div
        ref="imageContainer"
        class="image-container"
        :class="{ 'grabbing': isPanning }"
        @mousedown="handleCanvasMouseDown"
      >
        <div ref="imageCanvas" class="image-canvas" :class="{ loaded: imageLoaded }">
          <img
            ref="imagePreview"
            :src="imageUrl"
            alt="预览图片"
            class="image-element"
            @load="onImageLoad"
          />
          <div ref="bboxOverlays" class="bbox-overlays">
            <div
              v-for="bbox in bboxes"
              :key="getPathKey(bbox.path)"
              class="bbox-overlay"
              :class="{
                visible: isBboxVisible(bbox.path),
                selected: isSelectedBbox(bbox.path)
              }"
              :data-path="JSON.stringify(bbox.path)"
              :style="{
                left: bbox.bbox[0] + 'px',
                top: bbox.bbox[1] + 'px',
                width: (bbox.bbox[2] - bbox.bbox[0]) + 'px',
                height: (bbox.bbox[3] - bbox.bbox[1]) + 'px'
              }"
              @mousedown="handleBboxMouseDown($event, bbox.path)"
            >
              <!-- 8 点调整手柄 -->
              <div
                v-if="isSelectedBbox(bbox.path)"
                v-for="handle in ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w']"
                :key="handle"
                class="resize-handle"
                :class="handle"
                :data-handle="handle"
              ></div>
            </div>
          </div>
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
  background: var(--bili-card-bg, #ffffff);
  border-radius: 10px;
  overflow: hidden;
}

.image-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  background: var(--bili-bg, #f4f5f7);
  border-bottom: 1px solid var(--bili-border, #e3e5e7);
  font-size: 12px;
  color: var(--bili-text-secondary, #9499a0);
  flex-shrink: 0;

  .image-path {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .image-actions {
    display: flex;
    gap: 8px;
  }

  .btn-sm {
    padding: 4px 10px;
    font-size: 12px;
    border: none;
    border-radius: 6px;
    background: var(--bili-card-bg, #ffffff);
    color: var(--bili-text-primary, #212121);
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: var(--bili-border, #e3e5e7);
    }

    &.active {
      background: var(--bili-pink, #fb7299);
      color: white;
    }
  }
}

.image-wrapper {
  flex: 1;
  overflow: auto;
  padding: 15px;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  background: var(--bili-bg, #f4f5f7);
  min-width: 0;
  min-height: 0;
}

.image-container {
  position: relative;
  display: inline-block;

  &.grabbing {
    cursor: grabbing !important;
  }
}

.image-canvas {
  position: relative;
  display: inline-block;
  transform-origin: center center;
  transition: transform 0.1s ease-out;

  // 确保画布尺寸与图片自然尺寸一致
  &.loaded {
    min-width: 100%;
    min-height: 100%;
  }
}

.image-element {
  display: block;
  border-radius: 6px;
  pointer-events: none;
  transform-origin: center center;
  // 图片以自然尺寸显示，不压缩
  max-width: none;
  height: auto;
}

.bbox-overlays {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  // 确保覆盖层与图片自然尺寸一致
  width: 100%;
  height: 100%;
}

.bbox-overlay {
  position: absolute;
  border: 2px solid var(--bili-pink, #fb7299);
  background-color: rgba(251, 114, 153, 0.15);
  box-sizing: border-box;
  pointer-events: auto;
  cursor: pointer;
  display: none;

  &.visible {
    display: block;
  }

  &.selected {
    background-color: rgba(251, 114, 153, 0.25);
    border-color: var(--bili-pink, #fb7299);
  }

  &:hover {
    background-color: rgba(251, 114, 153, 0.3);
  }
}

.resize-handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--bili-pink, #fb7299);
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

/* 放大模式 */
.zoom-mode {
  .image-container {
    cursor: grab;
  }

  .grabbing {
    cursor: grabbing !important;
  }

  .bbox-overlay {
    pointer-events: none;
  }
}
</style>
