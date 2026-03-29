<script setup lang="ts">
/**
 * BboxPropertyEditor v4 - BBox 属性编辑器
 *
 * 功能：
 * - 左侧：BBox 列表/树形导航（支持拖拽排序）
 * - 右侧：当前选中 bbox 的属性编辑
 * - 自动检测树形/列表模式
 */
import { computed, ref } from 'vue'
import { useAnnotationContext } from '@/composables/useAnnotationContext'

// Props
const props = defineProps<{
  readonly?: boolean
}>()

// 获取上下文
const context = useAnnotationContext()
const {
  bboxList,
  selectedId,
  config,
  addBbox,
  deleteBbox,
  selectBbox
} = context

// 是否树形模式
const isTreeMode = computed(() => {
  return !!(config.value?.bboxSource?.childrenField)
})

// 显示字段
const displayField = computed(() => {
  return config.value?.bboxSource?.displayField || 'type'
})

// 获取显示文本
const getDisplayText = (bbox: any) => {
  return bbox[displayField.value] || `BBox ${bbox.id}`
}

// 展开状态（使用路径而非 ID，避免 parseBboxList 后 ID 变化导致状态丢失）
const expandedPaths = ref<Set<string>>(new Set())

// 获取路径的字符串 key
const getPathKey = (bbox: any) => bbox.path.join('-')

// 切换展开
const toggleExpand = (bbox: any, event: Event) => {
  event.stopPropagation()
  const pathKey = getPathKey(bbox)
  if (expandedPaths.value.has(pathKey)) {
    expandedPaths.value.delete(pathKey)
  } else {
    expandedPaths.value.add(pathKey)
  }
}

const isExpanded = (bbox: any) => expandedPaths.value.has(getPathKey(bbox))

// 选中节点
const handleSelect = (id: string) => {
  selectBbox(id)
}

// 判断是否选中
const isSelected = (id: string) => selectedId.value === id

// ===== 拖拽状态 =====
const draggedId = ref<string | null>(null)
const dragOverId = ref<string | null>(null)
const dropPosition = ref<'before' | 'after' | 'child' | null>(null)

// 工具函数：获取包含节点的数组容器和索引
// path = [0] -> 返回 { container: 根数组, index: 0 }
// path = [0, 1] -> 返回 { container: 根数组[0].children, index: 1 }
// path = [0, 1, 2] -> 返回 { container: 根数组[0].children[1].children, index: 2 }
function getNodeContainer(dataArray: any[], path: number[], childrenField: string): { container: any[], index: number } | null {
  if (path.length === 0) return null

  if (path.length === 1) {
    // 根数组中的元素
    return { container: dataArray, index: path[0] }
  }

  // path.length >= 2，需要通过 children 导航到父容器
  let node = dataArray[path[0]]
  for (let i = 1; i < path.length - 1; i++) {
    if (!node || !node[childrenField]) return null
    node = node[childrenField][path[i]]
  }

  if (!node || !node[childrenField] || !Array.isArray(node[childrenField])) return null

  return { container: node[childrenField], index: path[path.length - 1] }
}

// 开始拖拽
const handleDragStart = (e: DragEvent, id: string) => {
  if (props.readonly) return
  draggedId.value = id
  e.dataTransfer!.effectAllowed = 'move'
  e.dataTransfer!.setData('text/plain', id)
}

// 拖拽经过
const handleDragOver = (e: DragEvent, bbox: any) => {
  if (props.readonly || draggedId.value === bbox.id) return
  e.preventDefault()
  dragOverId.value = bbox.id

  // 判断放置位置
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const y = e.clientY - rect.top
  const height = rect.height
  const xPercent = (e.clientX - rect.left) / rect.width

  // 拖到右侧（超过70%）就变成子节点
  if (xPercent > 0.7) {
    dropPosition.value = 'child'
  } else if (y < height * 0.5) {
    dropPosition.value = 'before'
  } else {
    dropPosition.value = 'after'
  }
}

// 拖拽离开 - 只在真正离开整个元素区域时才清除
const handleDragLeave = (e: DragEvent) => {
  // 检查是否进入了子元素（子元素也会触发 dragleave）
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const relatedTarget = e.relatedTarget as HTMLElement
  if (relatedTarget) {
    // 如果进入了当前元素的子元素，不清除状态
    if (relatedTarget.closest('.tree-node') === e.currentTarget) {
      return
    }
  }
  dragOverId.value = null
  dropPosition.value = null
}

// 执行拖拽 - 修改原始数据
const handleDrop = async (e: DragEvent, targetBbox: any) => {
  if (props.readonly || !draggedId.value) return
  e.preventDefault()

  // 获取被拖拽的 bbox
  const draggedBbox = bboxList.value.find(b => b.id === draggedId.value)
  if (!draggedBbox || draggedBbox.id === targetBbox.id) {
    resetDragState()
    return
  }

  // 如果 dropPosition 被清除，重新计算
  if (!dropPosition.value) {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    const y = e.clientY - rect.top
    const height = rect.height
    const xPercent = (e.clientX - rect.left) / rect.width

    if (xPercent > 0.7) {
      dropPosition.value = 'child'
    } else if (y < height * 0.5) {
      dropPosition.value = 'before'
    } else {
      dropPosition.value = 'after'
    }
  }

  // 获取原始数据路径
  const dataPath = config.value?.bboxSource?.dataPath || ''
  const childrenField = config.value?.bboxSource?.childrenField || 'children'
  const rawData = context.rawData.value

  // 获取数据数组
  let dataArray: any[] | null = null
  if (dataPath) {
    const segments = dataPath.match(/[^.[\]]+|\[\d+\]/g) || []
    let current = rawData
    for (const seg of segments) {
      if (current === null || current === undefined) break
      if (seg.startsWith('[') && seg.endsWith(']')) {
        current = current[parseInt(seg.slice(1, -1))]
      } else {
        current = current[seg]
      }
    }
    dataArray = Array.isArray(current) ? current : null
  } else {
    dataArray = Array.isArray(rawData) ? rawData : null
  }

  if (!dataArray) {
    resetDragState()
    return
  }

  // 获取被拖拽节点和目标节点的容器信息
  const draggedContainerInfo = getNodeContainer(dataArray, draggedBbox.path, childrenField)
  const targetContainerInfo = getNodeContainer(dataArray, targetBbox.path, childrenField)

  if (!draggedContainerInfo || !targetContainerInfo) {
    resetDragState()
    return
  }

  // 获取被拖拽的节点数据（必须在修改数组之前获取！）
  const draggedNode = draggedContainerInfo.container[draggedContainerInfo.index]

  // 检查是否拖拽到自己的子节点
  if (dropPosition.value === 'child') {
    const targetPath = targetBbox.path
    const draggedPath = draggedBbox.path
    if (draggedPath.length < targetPath.length) {
      let isAncestor = true
      for (let i = 0; i < draggedPath.length; i++) {
        if (draggedPath[i] !== targetPath[i]) {
          isAncestor = false
          break
        }
      }
      if (isAncestor) {
        resetDragState()
        return
      }
    }
  }

  // 执行移动
  if (dropPosition.value === 'child') {
    // 放入目标节点的 children 中
    const targetNode = targetContainerInfo.container[targetContainerInfo.index]
    if (!targetNode[childrenField]) {
      targetNode[childrenField] = []
    }

    // 判断是否拖到自己身上
    if (draggedContainerInfo.container === targetNode[childrenField]) {
      resetDragState()
      return
    }

    // 先添加到目标的 children
    targetNode[childrenField].push(draggedNode)
    // 再从原位置移除
    draggedContainerInfo.container.splice(draggedContainerInfo.index, 1)
  } else {
    // before/after 移动
    const sameContainer = draggedContainerInfo.container === targetContainerInfo.container

    // 先从原位置移除
    draggedContainerInfo.container.splice(draggedContainerInfo.index, 1)

    if (sameContainer) {
      // 同一容器内移动，需要调整索引
      let newIndex = targetContainerInfo.index
      if (dropPosition.value === 'after') {
        newIndex = targetContainerInfo.index + 1
      }
      // 因为先删除了，原位置在目标之前时索引需要-1
      if (draggedContainerInfo.index < targetContainerInfo.index) {
        newIndex = Math.max(0, newIndex - 1)
      }
      targetContainerInfo.container.splice(newIndex, 0, draggedNode)
    } else {
      // 跨容器移动
      let newIndex = targetContainerInfo.index
      if (dropPosition.value === 'after') {
        newIndex = targetContainerInfo.index + 1
      }
      targetContainerInfo.container.splice(newIndex, 0, draggedNode)
    }
  }

  // 重新解析 bboxList
  context.parseBboxList()

  resetDragState()
}

const resetDragState = () => {
  draggedId.value = null
  dragOverId.value = null
  dropPosition.value = null
}

// 拖拽结束清理
const handleDragEnd = () => {
  resetDragState()
}

// ===== 获取节点的子节点数量（直接子节点） =====
const getChildrenCount = (bbox: any): number => {
  const childrenField = config.value?.bboxSource?.childrenField
  if (!childrenField || !context.rawData.value) return 0

  const dataPath = config.value?.bboxSource?.dataPath || ''
  let node: any = context.rawData.value

  // 先导航到数据数组
  if (dataPath) {
    const segments = dataPath.match(/[^.[\]]+|\[\d+\]/g) || []
    for (const seg of segments) {
      if (node === null || node === undefined) return 0
      if (seg.startsWith('[') && seg.endsWith(']')) {
        node = node[parseInt(seg.slice(1, -1))]
      } else {
        node = node[seg]
      }
    }
  }

  if (!Array.isArray(node)) return 0

  // 根据路径找到对应节点（树形结构需要通过 childrenField 访问）
  // path[0] 是根数组的索引
  // path[1] 是 node[path[0]].children[path[1]]
  // path[2] 是 node[path[0]].children[path[1]].children[path[2]]
  // 以此类推
  node = node[bbox.path[0]]
  for (let i = 1; i < bbox.path.length; i++) {
    if (!node || !node[childrenField] || !Array.isArray(node[childrenField])) return 0
    node = node[childrenField][bbox.path[i]]
  }

  if (!node || !node[childrenField]) return 0
  return Array.isArray(node[childrenField]) ? node[childrenField].length : 0
}

// ===== 判断拖拽状态 =====
const isDragging = (id: string) => draggedId.value === id
const isDragOver = (id: string) => dragOverId.value === id
const getDropClass = (id: string) => {
  if (!isDragOver(id)) return ''
  return dropPosition.value || ''
}

// 新建 bbox（根级）
const handleAdd = () => {
  addBbox()
}

// 新建 bbox（指定父节点）
const handleAddChild = (parentBbox: any) => {
  // 记住父节点路径
  const parentPath = parentBbox.path

  // 添加新节点
  addBbox([0, 0, 100, 100], parentPath)

  // 重新解析后，展开从根到父节点的所有节点（使用路径而非 ID）
  for (let len = 1; len <= parentPath.length; len++) {
    const ancestorPath = parentPath.slice(0, len)
    expandedPaths.value.add(ancestorPath.join('-'))
  }
}

// 删除 bbox
const handleDelete = (id: string) => {
  deleteBbox(id)
}

// 计算节点的层级深度
const getLevel = (bbox: any): number => {
  return bbox.path.length
}

// ===== 树形显示过滤 =====
// 检查一个节点是否应该显示（其父节点路径上所有节点都展开）
const shouldShowNode = (bbox: any): boolean => {
  // 根节点始终显示
  if (bbox.path.length <= 1) return true

  // 检查所有父节点是否展开
  for (let i = 1; i < bbox.path.length; i++) {
    // 构建父节点的 path
    const parentPath = bbox.path.slice(0, i)
    const parentPathKey = parentPath.join('-')

    // 找到父节点
    const parentBbox = bboxList.value.find(b => b.path.join('-') === parentPathKey)
    if (parentBbox && !isExpanded(parentBbox)) {
      return false
    }
  }
  return true
}

// 过滤出应该显示的 bbox（用于树形模式）
const visibleBboxList = computed(() => {
  if (!isTreeMode.value) return bboxList.value
  return bboxList.value.filter(bbox => shouldShowNode(bbox))
})
</script>

<template>
  <div class="bbox-property-editor">
    <!-- 左侧：导航列表 -->
    <div class="nav-panel">
      <div class="nav-header">
        <span class="nav-title">框</span>
        <button class="btn-add" @click="handleAdd" :disabled="readonly" title="新建">
          +
        </button>
      </div>

      <div class="nav-content">
        <!-- 空状态 -->
        <div v-if="bboxList.length === 0" class="empty-nav">
          <p>暂无数据</p>
          <button class="btn-add-empty" @click="handleAdd" :disabled="readonly">
            添加第一个节点
          </button>
        </div>

        <!-- 树形模式 -->
        <template v-else-if="isTreeMode">
          <div
            v-for="bbox in visibleBboxList"
            :key="bbox.id"
            class="tree-node"
            :class="[
              { selected: isSelected(bbox.id) },
              { dragging: isDragging(bbox.id) },
              { dragover: isDragOver(bbox.id) },
              getDropClass(bbox.id)
            ]"
            :data-level="getLevel(bbox)"
            :draggable="!readonly"
            @dragstart="handleDragStart($event, bbox.id)"
            @dragover="handleDragOver($event, bbox)"
            @dragleave="handleDragLeave($event)"
            @drop="handleDrop($event, bbox)"
            @dragend="handleDragEnd"
            @click="handleSelect(bbox.id)"
          >
            <!-- 展开/折叠按钮 -->
            <button
              v-if="getChildrenCount(bbox) > 0"
              class="expand-btn"
              @click.stop="toggleExpand(bbox, $event)"
            >
              {{ isExpanded(bbox) ? '▼' : '▶' }}
            </button>
            <span v-else class="expand-placeholder"></span>

            <!-- 标签区域 -->
            <div class="node-content">
              <span class="node-label">{{ getDisplayText(bbox) }}</span>
            </div>

            <!-- 操作按钮组 -->
            <div class="node-actions">
              <button
                class="action-btn add-btn"
                @click.stop="handleAddChild(bbox)"
                :disabled="readonly"
                title="添加子节点"
              >+</button>
              <button
                class="action-btn delete-btn"
                @click.stop="handleDelete(bbox.id)"
                :disabled="readonly"
                title="删除"
              >×</button>
            </div>
          </div>
        </template>

        <!-- 列表模式 -->
        <template v-else>
          <div
            v-for="bbox in bboxList"
            :key="bbox.id"
            class="list-item"
            :class="{ selected: isSelected(bbox.id), dragging: isDragging(bbox.id) }"
            :draggable="!readonly"
            @dragstart="handleDragStart($event, bbox.id)"
            @dragover="handleDragOver($event, bbox)"
            @dragleave="handleDragLeave($event)"
            @drop="handleDrop($event, bbox)"
            @dragend="handleDragEnd"
            @click="handleSelect(bbox.id)"
          >
            <span class="item-label">{{ getDisplayText(bbox) }}</span>
            <button
              class="action-btn delete-btn"
              @click.stop="handleDelete(bbox.id)"
              :disabled="readonly"
              title="删除"
            >×</button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bbox-property-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #FFFFFF;
  overflow: hidden;
}

/* 导航 */
.nav-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.nav-title {
  font-weight: 600;
  font-size: 13px;
  color: #374151;
}

.nav-content {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.btn-add {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: #165DFF;
  color: white;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-add:hover:not(:disabled) {
  background: #0E42D2;
}

.btn-add:disabled {
  background: #E5E7EB;
  cursor: not-allowed;
}

/* 树节点样式 */
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  margin-bottom: 4px;
  margin-left: 0;
  border-radius: 8px;
  background: #F3F4F6;
  cursor: pointer;
  transition: all 0.15s;
  border: 2px solid transparent;
  user-select: none;
  position: relative;
}

/* 层级缩进 - 每层 24px */
.tree-node[data-level="1"] { margin-left: 8px; }
.tree-node[data-level="2"] { margin-left: 32px; }
.tree-node[data-level="3"] { margin-left: 56px; }
.tree-node[data-level="4"] { margin-left: 80px; }
.tree-node[data-level="5"] { margin-left: 104px; }

.tree-node:hover {
  background: #E5E7EB;
}

.tree-node.selected {
  background: #E8F3FF;
  border-color: #165DFF;
}

.tree-node.dragging {
  opacity: 0.5;
  background: #FFF7ED;
}

.tree-node.dragover {
  background: #FEF3C7;
}

.tree-node.before {
  border-top-color: #165DFF;
  border-top-style: solid;
}

.tree-node.after {
  border-bottom-color: #165DFF;
  border-bottom-style: solid;
}

.tree-node.child {
  background: #DBEAFE;
  border-color: #165DFF;
}

.expand-btn {
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #6B7280;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

.expand-btn:hover {
  background: #E5E7EB;
  color: #165DFF;
}

.expand-placeholder {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.node-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.node-label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-bbox {
  font-size: 11px;
  color: #9CA3AF;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.tree-node:hover .node-actions,
.tree-node.selected .node-actions {
  opacity: 1;
}

.action-btn {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.add-btn {
  background: #E8F3FF;
  color: #165DFF;
}

.add-btn:hover:not(:disabled) {
  background: #165DFF;
  color: white;
}

.delete-btn {
  background: transparent;
  color: #9CA3AF;
}

.delete-btn:hover:not(:disabled) {
  background: #FEE2E2;
  color: #EF4444;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 列表模式 */
.list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  background: #F3F4F6;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
  transition: all 0.15s;
  user-select: none;
  border: 2px solid transparent;
}

.list-item:hover {
  background: #E5E7EB;
}

.list-item.selected {
  background: #E8F3FF;
  border-color: #165DFF;
}

.list-item.dragging {
  opacity: 0.5;
}

.list-item .item-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-item .action-btn {
  opacity: 0;
}

.list-item:hover .action-btn,
.list-item.selected .action-btn {
  opacity: 1;
}

.empty-nav {
  text-align: center;
  color: #9CA3AF;
  padding: 40px 20px;
  font-size: 13px;
}

.btn-add-empty {
  margin-top: 12px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: #165DFF;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-add-empty:hover:not(:disabled) {
  background: #0E42D2;
}

.btn-add-empty:disabled {
  background: #E5E7EB;
  cursor: not-allowed;
}
</style>