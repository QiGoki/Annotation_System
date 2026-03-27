/**
 * 标注模块类型定义
 *
 * 架构说明：
 * - 每个组件需要声明它需要的字段（schema）
 * - 每个组件需要提供 fieldMapping 函数，用于智能推荐字段绑定
 * - 运行时通过 fieldBindings 将 JSON 数据绑定到组件
 */

/**
 * 字段 Schema 定义
 * 组件声明它需要哪些数据字段
 */
export interface FieldSchema {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  label: string
  required?: boolean
  default?: any
  description?: string
}

/**
 * 模块 Schema
 */
export interface ModuleSchema {
  fields: Record<string, FieldSchema>
}

/**
 * fieldMapping 函数类型
 * 接收原始数据，返回推荐的数据值
 */
export type FieldMappingFn = (data: any) => any

/**
 * 模块定义（组件注册到市场时的格式）
 */
export interface ModuleDefinition {
  id: string                              // 组件唯一标识
  name: string                            // 组件名称
  icon: string                            // 图标
  description?: string                    // 描述
  component: any                          // Vue 组件
  schema: ModuleSchema                    // 声明需要的字段
  fieldMapping: Record<string, FieldMappingFn>  // 智能推荐函数
  defaultProps?: Record<string, any>      // 默认属性
}

/**
 * 模块实例配置（用户在配置器中保存的配置）
 */
export interface ModuleInstance {
  id: string                              // 实例 ID
  type: string                            // 模块类型（对应 ModuleDefinition.id）
  col: number                             // 列位置 (1=左，2=中，3=右)
  row: number                             // 行位置
  width: string                           // 宽度 (如 '60%', '350px')
  height: string                          // 高度
  fieldBindings: Record<string, string>   // 字段绑定 { fieldName: jsonPath }
  props: Record<string, any>              // 组件属性
}

/**
 * 页面配置
 */
export interface PageConfig {
  modules: ModuleInstance[]
  layout?: LayoutConfig
}

/**
 * 布局配置
 */
export interface LayoutConfig {
  columnCount: number                     // 列数（默认 3）
  columns: ColumnConfig[]                 // 各列配置
}

/**
 * 列配置
 */
export interface ColumnConfig {
  index: number                           // 列索引 (1-based)
  width: string                           // 宽度百分比，如 '25%', '40%'
  label?: string                          // 列标签，如 '左列', '中列', '右列'
}

/**
 * 标注项目配置
 */
export interface AnnotationProjectConfig {
  projectId: string
  name: string
  type: string
  pageConfig: PageConfig
  outputConfig?: {
    format: 'jsonl' | 'json'
    fields?: string[]
  }
}

/**
 * 解析后的字段（用于字段提取 UI 展示）
 */
export interface ParsedField {
  path: string          // JSONPath，如 'image', 'components[0].bbox'
  type: string          // 类型
  sampleValue?: any     // 示例值
  length?: number       // 数组长度（如果是数组）
  preview?: string      // 对象预览（如果是对象）
}

/**
 * 自定义字段解析规则
 */
export interface CustomFieldRule {
  name: string                      // 自定义字段名称
  ruleType: 'path' | 'regex'        // 规则类型
  path?: string                     // JSONPath（当 ruleType 为 path 时）
  regex?: string                    // 正则表达式（当 ruleType 为 regex 时）
  regexSource?: string              // 正则匹配的源字段路径
  targetField?: string              // 目标字段名（用于 regex 匹配后的结果存储）
}
