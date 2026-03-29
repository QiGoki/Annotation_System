/**
 * 标注上下文 - 共享状态管理
 *
 * 用于组件间数据共享和交互状态同步
 */
import { ref, computed, provide, inject, type Ref, type ComputedRef } from 'vue'
import type { BboxItem, BboxCoord, ImageBBoxAnnotatorConfig } from '@/types/annotation-module'

// ==================== 类型定义 ====================

export interface AnnotationContext {
  // ===== 原始数据 =====
  rawData: Ref<any>

  // ===== 配置 =====
  config: Ref<ImageBBoxAnnotatorConfig | null>

  // ===== BBox 数据 =====
  bboxList: Ref<BboxItem[]>

  // ===== 交互状态 =====
  selectedId: Ref<string | null>
  showAllBboxes: Ref<boolean>

  // ===== 计算属性 =====
  selectedBbox: ComputedRef<BboxItem | null>
  representField: ComputedRef<string>

  // ===== 方法 =====
  setRawData(data: any): void
  setConfig(cfg: ImageBBoxAnnotatorConfig): void
  parseBboxList(): void
  updateBbox(id: string, field: string, value: any): void
  updateBboxCoord(id: string, bbox: BboxCoord): void
  addBbox(bbox?: BboxCoord, parentPath?: number[]): number[] | null
  deleteBbox(id: string): void
  selectBbox(id: string | null): void
  getOutputData(): any[]
  reset(): void
}

// Context Key
const AnnotationContextKey = Symbol('annotation-context')

// ==================== ID 生成器 ====================

let idCounter = 0
const generateId = () => `bbox_${++idCounter}`

// ==================== 数据解析器 ====================

/**
 * 根据 JSONPath 获取值
 */
function getValueByPath(data: any, path: string): any {
  if (!path) return data

  const segments = path.match(/[^.[\]]+|\[\d+\]/g) || []
  let result = data

  for (const seg of segments) {
    if (result === null || result === undefined) return undefined
    if (seg.startsWith('[') && seg.endsWith(']')) {
      result = result[parseInt(seg.slice(1, -1))]
    } else {
      result = result[seg]
    }
  }

  return result
}

/**
 * 从字符串中提取 bbox
 */
function extractBboxesFromString(
  text: string,
  regex: string
): { bbox: BboxCoord; sourceText: string }[] {
  const results: { bbox: BboxCoord; sourceText: string }[] = []
  const regexObj = new RegExp(regex, 'g')

  let match
  while ((match = regexObj.exec(text)) !== null) {
    const coordStr = match[1] || match[0]
    const nums = coordStr.match(/\d+/g)
    if (nums && nums.length >= 4) {
      results.push({
        bbox: [parseInt(nums[0]), parseInt(nums[1]), parseInt(nums[2]), parseInt(nums[3])],
        sourceText: match[0]
      })
    }
  }

  return results
}

/**
 * 从列表数据解析 bbox（支持树形递归）
 */
function parseBboxFromList(
  data: any[],
  config: ImageBBoxAnnotatorConfig,
  parentPath: number[] = []
): BboxItem[] {
  const { bboxSource, bboxProperties } = config
  const bboxField = bboxSource.bboxField || 'bbox'
  const childrenField = bboxSource.childrenField
  const result: BboxItem[] = []

  data.forEach((item, index) => {
    const currentPath = [...parentPath, index]

    // 提取 bbox
    const bbox = item[bboxField]
    if (Array.isArray(bbox) && bbox.length >= 4) {
      const bboxItem: BboxItem = {
        id: generateId(),
        path: currentPath,
        bbox: [bbox[0], bbox[1], bbox[2], bbox[3]]
      }

      // 提取属性
      for (const prop of bboxProperties) {
        bboxItem[prop.name] = item[prop.sourceField] ?? prop.defaultValue
      }

      result.push(bboxItem)
    }

    // 递归处理子节点
    if (childrenField && item[childrenField] && Array.isArray(item[childrenField])) {
      result.push(...parseBboxFromList(item[childrenField], config, currentPath))
    }
  })

  return result
}

// ==================== Context 创建 ====================

/**
 * 创建标注上下文（由父组件调用）
 */
export function createAnnotationContext(): AnnotationContext {
  // 原始数据
  const rawData = ref<any>(null)

  // 配置
  const config = ref<ImageBBoxAnnotatorConfig | null>(null)

  // BBox 数据
  const bboxList = ref<BboxItem[]>([])

  // 交互状态
  const selectedId = ref<string | null>(null)
  const showAllBboxes = ref(false)

  // 计算属性
  const selectedBbox = computed(() =>
    bboxList.value.find(b => b.id === selectedId.value) || null
  )

  const representField = computed(() =>
    config.value?.representField || 'type'
  )

  // ===== 方法实现 =====

  const setRawData = (data: any) => {
    rawData.value = data
    if (config.value) {
      parseBboxList()
    }
  }

  const setConfig = (cfg: ImageBBoxAnnotatorConfig) => {
    config.value = cfg
    if (rawData.value) {
      parseBboxList()
    }
  }

  const parseBboxList = () => {
    if (!rawData.value || !config.value) {
      bboxList.value = []
      return
    }

    const cfg = config.value
    const data = rawData.value
    const result: BboxItem[] = []

    if (cfg.bboxSource.mode === 'list') {
      const listData = getValueByPath(data, cfg.bboxSource.dataPath || '')
      if (Array.isArray(listData)) {
        result.push(...parseBboxFromList(listData, cfg))
      }
    } else if (cfg.bboxSource.mode === 'string') {
      const stringValue = getValueByPath(data, cfg.bboxSource.stringPath || '')
      if (typeof stringValue === 'string' && cfg.bboxSource.extractRegex) {
        const extracted = extractBboxesFromString(stringValue, cfg.bboxSource.extractRegex)
        extracted.forEach((item, index) => {
          const bboxItem: BboxItem = {
            id: generateId(),
            path: [index],
            bbox: item.bbox
          }
          // 提取属性
          for (const prop of cfg.bboxProperties) {
            bboxItem[prop.name] = getValueByPath(data, prop.sourceField) ?? prop.defaultValue
          }
          result.push(bboxItem)
        })
      }
    }

    bboxList.value = result
  }

  const updateBbox = (id: string, field: string, value: any) => {
    const index = bboxList.value.findIndex(b => b.id === id)
    if (index >= 0) {
      // 使用解构创建新对象，确保响应式更新
      bboxList.value[index] = {
        ...bboxList.value[index],
        [field]: value
      }
    }
  }

  const updateBboxCoord = (id: string, bbox: BboxCoord) => {
    const item = bboxList.value.find(b => b.id === id)
    if (item) {
      item.bbox = bbox
    }
  }

  const addBbox = (bbox?: BboxCoord, parentPath?: number[]): number[] | null => {
    if (!config.value || !rawData.value) return null

    const childrenField = config.value.bboxSource?.childrenField || 'children'
    const bboxField = config.value.bboxSource?.bboxField || 'bbox'
    const dataPath = config.value.bboxSource?.dataPath || ''
    const bboxProperties = config.value.bboxProperties || []

    // 获取数据数组
    let dataArray: any
    if (dataPath) {
      const segments = dataPath.match(/[^.[\]]+|\[\d+\]/g) || []
      dataArray = rawData.value
      for (const seg of segments) {
        if (dataArray === null || dataArray === undefined) return null
        if (seg.startsWith('[') && seg.endsWith(']')) {
          dataArray = dataArray[parseInt(seg.slice(1, -1))]
        } else {
          dataArray = dataArray[seg]
        }
      }
    } else {
      dataArray = rawData.value
    }

    if (!Array.isArray(dataArray)) return null

    // 计算新节点的路径
    let newPath: number[]
    if (parentPath && parentPath.length > 0) {
      // 找到父节点
      let parentNode: any = dataArray[parentPath[0]]
      for (let i = 1; i < parentPath.length; i++) {
        if (!parentNode || !parentNode[childrenField]) return null
        parentNode = parentNode[childrenField][parentPath[i]]
      }
      if (!parentNode) return null
      if (!parentNode[childrenField]) {
        parentNode[childrenField] = []
      }
      newPath = [...parentPath, parentNode[childrenField].length]
      // 添加到父节点的 children
      const newNode: any = {
        [bboxField]: bbox || [0, 0, 100, 100]
      }
      // 只有配置了 childrenField 才添加 children 数组
      if (config.value.bboxSource?.childrenField) {
        newNode[childrenField] = []
      }
      for (const prop of bboxProperties) {
        newNode[prop.sourceField] = prop.defaultValue
      }
      parentNode[childrenField].push(newNode)
    } else {
      // 添加到根数组
      newPath = [dataArray.length]
      const newNode: any = {
        [bboxField]: bbox || [0, 0, 100, 100]
      }
      // 只有配置了 childrenField 才添加 children 数组
      if (config.value.bboxSource?.childrenField) {
        newNode[childrenField] = []
      }
      for (const prop of bboxProperties) {
        newNode[prop.sourceField] = prop.defaultValue
      }
      dataArray.push(newNode)
    }

    // 重新解析 bboxList
    parseBboxList()

    // 选中新建的节点
    const pathKey = newPath.join('-')
    const newBboxItem = bboxList.value.find(b => b.path.join('-') === pathKey)
    if (newBboxItem) {
      selectedId.value = newBboxItem.id
    }

    return newPath
  }

  const deleteBbox = (id: string) => {
    const bboxItem = bboxList.value.find(b => b.id === id)
    if (!bboxItem) return

    // 从 rawData 中删除节点
    if (config.value && rawData.value) {
      const childrenField = config.value.bboxSource?.childrenField || 'children'
      const dataPath = config.value.bboxSource?.dataPath || ''

      // 获取数据数组
      let dataArray: any
      if (dataPath) {
        const segments = dataPath.match(/[^.[\]]+|\[\d+\]/g) || []
        dataArray = rawData.value
        for (const seg of segments) {
          if (dataArray === null || dataArray === undefined) break
          if (seg.startsWith('[') && seg.endsWith(']')) {
            dataArray = dataArray[parseInt(seg.slice(1, -1))]
          } else {
            dataArray = dataArray[seg]
          }
        }
      } else {
        dataArray = rawData.value
      }

      if (Array.isArray(dataArray)) {
        // 根据 path 找到节点所在容器并删除
        const path = bboxItem.path
        if (path.length === 1) {
          // 根节点：直接从 dataArray 删除
          dataArray.splice(path[0], 1)
        } else if (path.length > 1) {
          // 子节点：导航到父容器
          let parentNode: any = dataArray[path[0]]
          for (let i = 1; i < path.length - 1; i++) {
            if (!parentNode || !parentNode[childrenField]) break
            parentNode = parentNode[childrenField][path[i]]
          }
          if (parentNode && parentNode[childrenField] && Array.isArray(parentNode[childrenField])) {
            parentNode[childrenField].splice(path[path.length - 1], 1)
          }
        }
      }
    }

    // 从 bboxList 中移除
    const index = bboxList.value.findIndex(b => b.id === id)
    if (index >= 0) {
      bboxList.value.splice(index, 1)
    }

    // 清除选中状态
    if (selectedId.value === id) {
      selectedId.value = null
    }
  }

  const selectBbox = (id: string | null) => {
    selectedId.value = id
  }

  const getOutputData = () => {
    if (!config.value) return []

    const fields = config.value.output.fields
    return bboxList.value.map(bbox => {
      const output: any = {}
      for (const field of fields) {
        output[field] = bbox[field]
      }
      return output
    })
  }

  const reset = () => {
    rawData.value = null
    bboxList.value = []
    selectedId.value = null
    showAllBboxes.value = false
  }

  const context: AnnotationContext = {
    rawData,
    config,
    bboxList,
    selectedId,
    showAllBboxes,
    selectedBbox,
    representField,
    setRawData,
    setConfig,
    parseBboxList,
    updateBbox,
    updateBboxCoord,
    addBbox,
    deleteBbox,
    selectBbox,
    getOutputData,
    reset
  }

  provide(AnnotationContextKey, context)
  return context
}

/**
 * 使用标注上下文（由子组件调用）
 */
export function useAnnotationContext(): AnnotationContext {
  const context = inject<AnnotationContext>(AnnotationContextKey)
  if (!context) {
    throw new Error('useAnnotationContext must be used within a provider')
  }
  return context
}