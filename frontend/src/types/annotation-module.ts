/**
 * 标注模块类型定义 v3
 *
 * 重构后的组件配置系统
 */

// ==================== 基础类型 ====================

/**
 * BBox 坐标格式 [x1, y1, x2, y2]
 */
export type BboxCoord = [number, number, number, number]

/**
 * 单个 BBox 数据项
 */
export interface BboxItem {
  id: string                    // 内部唯一 ID
  path: number[]                // 在原数据中的路径
  bbox: BboxCoord               // 坐标
  [key: string]: any            // 动态属性
}

// ==================== ConfigSchema 定义 ====================

/**
 * 字段选择类型（从解析的字段中选择）
 */
export interface FieldSelectSchema {
  type: 'field-select'
  label: string
  required?: boolean
  default?: string
  description?: string
}

/**
 * 基础字段类型
 */
export interface BaseFieldSchema {
  type: 'string' | 'number' | 'boolean'
  label: string
  required?: boolean
  default?: any
  description?: string
}

/**
 * 选择类型
 */
export interface SelectSchema {
  type: 'select'
  label: string
  options: string[] | { label: string; value: any }[]
  required?: boolean
  default?: string
}

/**
 * 对象类型（嵌套字段）
 */
export interface ObjectSchema {
  type: 'object'
  fields: Record<string, ConfigFieldSchema>
}

/**
 * 分组类型（UI 展示用）
 */
export interface GroupSchema {
  type: 'group'
  label: string
  fields: Record<string, ConfigFieldSchema>
}

/**
 * 数组类型
 */
export interface ArraySchema {
  type: 'array'
  label: string
  itemSchema: Record<string, ConfigFieldSchema>
}

/**
 * 字符串数组类型（textarea 编辑）
 */
export interface ArrayStringSchema {
  type: 'array-string'
  label: string
  description?: string
  default?: string[]
}

/**
 * 条件显示
 */
export interface ShowIfCondition {
  [field: string]: any
}

/**
 * 配置字段 Schema（联合类型）
 */
export type ConfigFieldSchema =
  | BaseFieldSchema
  | FieldSelectSchema
  | SelectSchema
  | ObjectSchema
  | GroupSchema
  | ArraySchema
  | ArrayStringSchema
  | (BaseFieldSchema & { showIf?: ShowIfCondition })
  | (FieldSelectSchema & { showIf?: ShowIfCondition })
  | (SelectSchema & { showIf?: ShowIfCondition })

// ==================== ImageBBoxAnnotator 配置 ====================

/**
 * 图片设置
 */
export interface ImageConfig {
  field: string                 // JSON 路径，如 "image"
  pathClean?: {
    enabled: boolean
    prefix: string              // 要清除的路径前缀
  }
}

/**
 * BBox 数据源配置
 */
export interface BboxSourceConfig {
  mode: 'list' | 'string'

  // list 模式
  dataPath?: string             // 数据路径
  bboxField?: string            // bbox 字段名
  childrenField?: string        // 子节点字段名（树形结构时使用）
  displayField?: string         // 显示字段名（树形结构时使用）

  // string 模式
  stringPath?: string           // 字符串字段路径
  extractRegex?: string         // 提取正则
}

/**
 * BBox 属性定义
 */
export interface BboxPropertyDef {
  name: string                  // 属性标识
  sourceField: string           // 来源字段
  displayName: string           // 显示名称
  defaultValue?: any            // 默认值
}

/**
 * 输出设置
 */
export interface OutputConfig {
  fields: string[]              // 需要输出的字段名
}

/**
 * ImageBBoxAnnotator 完整配置
 */
export interface ImageBBoxAnnotatorConfig {
  title: string
  image: ImageConfig
  bboxSource: BboxSourceConfig
  bboxProperties: BboxPropertyDef[]
  representField: string        // 代表属性字段名
  output: OutputConfig
}

// ==================== 模块定义系统 ====================

/**
 * 模块定义（组件注册到市场时的格式）
 */
export interface ModuleDefinition {
  id: string
  name: string
  icon: string
  description?: string
  component: any                          // Vue 组件

  // 新版：配置 Schema（用于配置面板渲染）
  configSchema?: Record<string, ConfigFieldSchema>
  defaultConfig?: any                     // 默认配置
}

/**
 * 模块实例配置（用户在配置器中保存的配置）
 */
export interface ModuleInstance {
  id: string                              // 实例 ID
  type: string                            // 模块类型
  col: number                             // 列位置
  row: number                             // 行位置
  width: string                           // 宽度
  height: string                          // 高度
  config?: ImageBBoxAnnotatorConfig | any // 模块配置
}

// ==================== 页面配置 ====================

/**
 * 数据源配置（用于保存和恢复）
 */
export interface DataSourceConfig {
  exampleJsonText?: string       // 原始 JSON 文本
  customFieldRules?: CustomFieldRule[] // 自定义字段规则
}

/**
 * 页面配置
 */
export interface PageConfig {
  modules: ModuleInstance[]
  layout?: LayoutConfig
  dataSource?: DataSourceConfig  // 数据源配置
}

/**
 * 布局配置
 */
export interface LayoutConfig {
  columnCount: number
  columns: ColumnConfig[]
  leftColumnWidth?: number  // 左列宽度（像素）
}

/**
 * 列配置
 */
export interface ColumnConfig {
  index: number
  width: string
  label?: string
  fill?: boolean  // 是否平铺满画布
}

// ==================== 辅助类型 ====================

/**
 * 解析后的字段（用于字段提取 UI 展示）
 */
export interface ParsedField {
  path: string
  type: string
  sampleValue?: any
  length?: number
  preview?: string
}

/**
 * 自定义字段解析规则
 */
export interface CustomFieldRule {
  name: string
  ruleType: 'path' | 'regex'
  path?: string
  regex?: string
  regexSource?: string
  targetField?: string
}