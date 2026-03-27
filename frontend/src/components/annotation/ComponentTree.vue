<script setup lang="ts">
/**
 * 组件树标注器组件
 * 支持功能：
 * - 树形结构展示组件层级
 * - 节点展开/折叠
 * - 点击节点选中组件
 * - 添加/删除/移动子组件
 * - 组件类型和文本显示
 */
import { ref, watch } from 'vue'

export interface ComponentNode {
  type: string
  text?: string
  bbox?: [number, number, number, number]
  children?: ComponentNode[]
}

export interface ComponentTreeProps {
  components: ComponentNode[]
  selectedPath?: number[] | null
  expandedPaths?: Record<string, boolean>
  readonly?: boolean
}

const props = withDefaults(defineProps<ComponentTreeProps>(), {
  selectedPath: null,
  readonly: false
})

const emit = defineEmits<{
  'update:selectedPath': [path: number[] | null]
  'update:components': [components: ComponentNode[]]
  'update:expandedPaths': [paths: Record<string, boolean>]
  'node:select': [path: number[], node: ComponentNode]
  'node:add': [parentPath: number[]]
  'node:delete': [path: number[]]
  'node:move': [path: number[], direction: number]
}>()

// 本地展开状态
const localExpandedPaths = ref<Record<string, boolean>>({})

// 使用 props 的展开状态或本地状态
const getExpandedPaths = () => props.expandedPaths || localExpandedPaths.value

// 更新展开状态
const updateExpandedPath = (path: number[], expanded: boolean) => {
  const pathKey = getPathKey(path)
  const newPaths = { ...getExpandedPaths(), [pathKey]: expanded }
  localExpandedPaths.value = newPaths
  emit('update:expandedPaths', newPaths)
}

// ========== 工具函数 ==========
const getPathKey = (path: number[]): string => path.join('-')

const findNode = (components: ComponentNode[], path: number[]): ComponentNode | null => {
  let current: any = components
  for (const index of path) {
    if (Array.isArray(current)) {
      current = current[index]
    } else if (current?.children && Array.isArray(current.children)) {
      current = current.children[index]
    } else {
      return null
    }
  }
  return current || null
}

const get_parentArray = (components: ComponentNode[], path: number[]): ComponentNode[] | null => {
  if (path.length === 0) return components

  let current: any = components
  for (let i = 0; i < path.length - 1; i++) {
    if (current?.children && Array.isArray(current.children)) {
      current = current.children[path[i]]
    } else {
      return null
    }
  }

  if (current?.children && Array.isArray(current.children)) {
    return current.children
  }
  return null
}

// ========== 节点操作 ==========
const selectNode = (path: number[], node: ComponentNode, event: MouseEvent) => {
  event.stopPropagation()
  emit('update:selectedPath', path)
  emit('node:select', path, node)
}

const toggleExpand = (path: number[], event: MouseEvent) => {
  event.stopPropagation()
  const pathKey = getPathKey(path)
  const currentExpanded = getExpandedPaths()[pathKey] !== false
  updateExpandedPath(path, !currentExpanded)
}

const addNode = (parentPath: number[], event: MouseEvent) => {
  event.stopPropagation()

  const parentArray = parentPath.length === 0
    ? props.components
    : get_parentArray(props.components, parentPath)

  if (!parentArray) return

  const newNode: ComponentNode = {
    type: 'button',
    text: '新组件',
    bbox: [0, 0, 100, 50],
    children: []
  }

  const newComponents = [...props.components]
  const targetArray = get_parentArray(newComponents, parentPath) || newComponents
  targetArray.push(newNode)

  // 展开父节点
  updateExpandedPath(parentPath, true)

  emit('update:components', newComponents)
  emit('node:add', parentPath)
}

const deleteNode = (path: number[], event: MouseEvent) => {
  event.stopPropagation()

  if (path.length === 0) return

  const newComponents = [...props.components]
  const parentArray = get_parentArray(newComponents, path)

  if (!parentArray) return

  const index = path[path.length - 1]
  parentArray.splice(index, 1)

  emit('update:components', newComponents)
  emit('node:delete', path)

  // 清除选中
  if (props.selectedPath && getPathKey(props.selectedPath) === getPathKey(path)) {
    emit('update:selectedPath', null)
  }
}

const moveNode = (path: number[], direction: number, event: MouseEvent) => {
  event.stopPropagation()

  const parentArray = get_parentArray(props.components, path)
  if (!parentArray) return

  const index = path[path.length - 1]
  const newIndex = index + direction

  if (newIndex < 0 || newIndex >= parentArray.length) return

  // 交换位置
  const temp = parentArray[index]
  parentArray[index] = parentArray[newIndex]
  parentArray[newIndex] = temp

  emit('update:components', [...props.components])
  emit('node:move', path, direction)
}

// ========== 渲染树节点 ==========
const renderNode = (node: ComponentNode, path: number[], level: number = 0) => {
  const pathKey = getPathKey(path)
  const isSelected = props.selectedPath && getPathKey(props.selectedPath) === pathKey
  const hasChildren = node.children && node.children.length > 0
  const isExpanded = getExpandedPaths()[pathKey] !== false

  return [
    // 节点
    h(
      'div',
      {
        class: ['tree-node', { selected: isSelected }],
        style: { paddingLeft: `${level * 18 + 10}px` },
        onClick: (e: MouseEvent) => selectNode(path, node, e)
      },
      [
        // 展开/折叠图标
        h(
          'span',
          {
            class: 'tree-expand',
            onClick: (e: MouseEvent) => toggleExpand(path, e)
          },
          hasChildren ? (isExpanded ? '▼' : '▶') : '•'
        ),

        // 类型标签
        h('span', { class: 'type-badge' }, node.type || '?'),

        // 文本预览
        h('span', { class: 'text-preview' }, (node.text || '').substring(0, 20)),

        // 操作按钮（非只读模式）
        !props.readonly ? h('span', { class: 'tree-actions' }, [
          h('button', {
            class: 'tree-btn-move',
            title: '上移',
            onClick: (e: MouseEvent) => moveNode(path, -1, e)
          }, '↑'),
          h('button', {
            class: 'tree-btn-move',
            title: '下移',
            onClick: (e: MouseEvent) => moveNode(path, 1, e)
          }, '↓'),
          h('button', {
            class: 'tree-btn-add',
            title: '添加子组件',
            onClick: (e: MouseEvent) => addNode(path, e)
          }, '+'),
          h('button', {
            class: 'tree-btn-del',
            title: '删除组件',
            onClick: (e: MouseEvent) => deleteNode(path, e)
          }, '−')
        ]) : null
      ]
    ),

    // 子节点
    hasChildren && isExpanded
      ? node.children!.map((child, index) => renderNode(child, [...path, index], level + 1))
      : null
  ]
}

// 手动导入 h 函数
import { h } from 'vue'

// 添加根组件
const addRootComponent = () => {
  const newNode: ComponentNode = {
    type: 'button',
    text: '新组件',
    bbox: [0, 0, 100, 50],
    children: []
  }

  emit('update:components', [...props.components, newNode])
  emit('node:add', [])
}

// 监听组件变化，重置展开状态
watch(() => props.components, () => {
  // 组件完全变化时可以选择保留或重置展开状态
}, { deep: true })
</script>

<template>
  <div class="component-tree">
    <div class="tree-header">
      <span class="tree-title">组件树</span>
      <button
        v-if="!readonly"
        class="btn-add-root"
        @click="addRootComponent"
        title="添加根组件"
      >
        + 添加根组件
      </button>
    </div>

    <div class="tree-content">
      <div v-if="components.length === 0" class="no-components">
        <p>暂无组件数据</p>
        <button v-if="!readonly" class="btn-add-first" @click="addRootComponent">
          添加第一个组件
        </button>
      </div>

      <div v-else class="tree-nodes">
        <template v-for="(node, index) in components" :key="index">
          <div class="tree-node-wrapper">
            <div
              :class="['tree-node', { selected: selectedPath && getPathKey(selectedPath) === getPathKey([index]) }]"
              @click="selectNode([index], node, $event)"
            >
              <span
                v-if="node.children && node.children.length > 0"
                class="tree-expand"
                @click.stop="toggleExpand([index], $event)"
              >
                {{ (getExpandedPaths()[getPathKey([index])] !== false) ? '▼' : '▶' }}
              </span>
              <span v-else class="tree-expand">•</span>

              <span class="type-badge">{{ node.type || '?' }}</span>
              <span class="text-preview">{{ (node.text || '').substring(0, 20) }}</span>

              <span v-if="!readonly" class="tree-actions">
                <button class="tree-btn-move" title="上移" @click.stop="moveNode([index], -1, $event)">↑</button>
                <button class="tree-btn-move" title="下移" @click.stop="moveNode([index], 1, $event)">↓</button>
                <button class="tree-btn-add" title="添加子组件" @click.stop="addNode([index], $event)">+</button>
                <button class="tree-btn-del" title="删除组件" @click.stop="deleteNode([index], $event)">−</button>
              </span>
            </div>

            <!-- 递归渲染子节点 -->
            <div
              v-if="node.children && node.children.length > 0 && (getExpandedPaths()[getPathKey([index])] !== false)"
              class="tree-children"
            >
              <ComponentTree
                :components="node.children"
                :selected-path="selectedPath?.slice(1)"
                :expanded-paths="getExpandedPaths()"
                :readonly="readonly"
                @update:selected-path="(path) => emit('update:selectedPath', path ? [index, ...path] : null)"
                @update:components="(newChildren) => {
                  const newComponents = [...components]
                  newComponents[index] = { ...node, children: newChildren }
                  emit('update:components', newComponents)
                }"
                @update:expanded-paths="(paths) => emit('update:expandedPaths', paths)"
                @node:add="(path) => emit('node:add', [index, ...path])"
                @node:delete="(path) => emit('node:delete', [index, ...path])"
                @node:move="(path, dir) => emit('node:move', [index, ...path], dir)"
                @node:select="(path, node) => emit('node:select', [index, ...path], node)"
              />
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.component-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bili-card-bg, #ffffff);
  border-radius: 10px;
  overflow: hidden;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid var(--bili-border, #e3e5e7);
  flex-shrink: 0;
}

.tree-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--bili-text-primary, #212121);
}

.btn-add-root {
  background: var(--bili-blue, #00aeeC);
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: var(--bili-blue-dark, #0096c7);
  }
}

.tree-content {
  flex: 1;
  overflow: auto;
  padding: 10px;
}

.no-components {
  text-align: center;
  color: var(--bili-text-secondary, #9499a0);
  padding: 40px 20px;

  p {
    margin: 0 0 15px 0;
    font-size: 14px;
  }
}

.btn-add-first {
  background: var(--bili-blue, #00aeeC);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;

  &:hover {
    background: var(--bili-blue-dark, #0096c7);
  }
}

.tree-nodes {
  min-height: 100%;
}

.tree-node-wrapper {
  margin: 2px 0;
}

.tree-node {
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
  white-space: nowrap;
  overflow: hidden;

  &:hover {
    background: var(--bili-bg, #f4f5f7);
  }

  &.selected {
    background: rgba(251, 114, 153, 0.1);
    border-left: 3px solid var(--bili-pink, #fb7299);
  }
}

.tree-expand {
  width: 14px;
  height: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: var(--bili-text-secondary, #9499a0);
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}

.type-badge {
  background: var(--bili-border, #e3e5e7);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--bili-text-secondary, #9499a0);
  flex-shrink: 0;
}

.text-preview {
  color: var(--bili-text-secondary, #9499a0);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.tree-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;

  .tree-node:hover & {
    opacity: 1;
  }
}

.tree-btn-move,
.tree-btn-add,
.tree-btn-del {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  font-size: 12px;
  border-radius: 3px;
  line-height: 1;
  transition: background 0.15s;
}

.tree-btn-move {
  color: var(--bili-text-secondary, #9499a0);

  &:hover {
    background: rgba(0, 0, 0, 0.05);
    color: var(--bili-text-primary, #212121);
  }
}

.tree-btn-add {
  color: var(--bili-blue, #00aeeC);

  &:hover {
    background: rgba(0, 174, 236, 0.1);
  }
}

.tree-btn-del {
  color: var(--bili-pink, #fb7299);

  &:hover {
    background: rgba(251, 114, 153, 0.1);
  }
}

.tree-children {
  margin-left: 18px;
  border-left: 1px dashed var(--bili-border, #e3e5e7);
  padding-left: 6px;
}
</style>
