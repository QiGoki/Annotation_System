/**
 * 标注工具类型定义
 */

/**
 * 标注工具配置
 */
export interface AnnotationTool {
  id: string
  name: string
  icon: string
  description?: string
  category: 'spatial' | 'text' | 'classification' | 'structural'
  // 工具组件的 props 定义
  propsSchema?: Record<string, ToolPropSchema>
  // 默认属性
  defaultProps?: Record<string, any>
}

/**
 * 工具属性 Schema
 */
export interface ToolPropSchema {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'select'
  label: string
  required?: boolean
  default?: any
  options?: { label: string; value: any }[]  // select 类型专用
  description?: string
}

/**
 * 工具实例配置（运行时）
 */
export interface ToolInstance {
  id: string           // 实例 ID
  toolId: string       // 工具类型 ID
  name: string         // 实例名称
  props: Record<string, any>  // 工具属性
  fieldBindings?: Record<string, string>  // 字段绑定
}

/**
 * 布局配置
 */
export interface LayoutConfig {
  left: ColumnConfig
  center: ColumnConfig
  right: ColumnConfig
}

/**
 * 列配置
 */
export interface ColumnConfig {
  panels: PanelConfig[]
  width?: string  // 列宽，如 '300px' 或 '25%'
}

/**
 * 面板配置
 */
export interface PanelConfig {
  id: string
  type: 'tool' | 'custom'
  toolId?: string       // 工具 ID（如果是工具面板）
  title: string
  collapsible?: boolean
  defaultExpanded?: boolean
  props?: Record<string, any>  // 面板属性
}

/**
 * 标注项目配置
 */
export interface AnnotationProjectConfig {
  id: string
  name: string
  description?: string
  type: string
  pageConfig: {
    layout: LayoutConfig
    tools: ToolInstance[]
  }
  outputConfig?: {
    format: 'jsonl' | 'json'
    fields?: string[]
  }
}

/**
 * 组件节点（标注数据结构）
 */
export interface ComponentNode {
  type: string
  text?: string
  bbox?: [number, number, number, number]  // [x1, y1, x2, y2]
  children?: ComponentNode[]
}

/**
 * Bbox 数据
 */
export interface BboxData {
  path: number[]        // 组件在树中的路径
  bbox: [number, number, number, number]
  type?: string
  text?: string
}

/**
 * 标注任务数据
 */
export interface AnnotationTaskData {
  id?: number
  projectId: number
  data: Record<string, any>  // 原始数据
  components?: ComponentNode[]  // 组件数据
  annotations?: Record<string, any>  // 标注结果
  _saved?: boolean  // 是否已保存
}
