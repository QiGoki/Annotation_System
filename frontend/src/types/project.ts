/**
 * 字段配置接口
 */
export interface FieldConfig {
  key: string
  path?: string
  regex?: string
}

/**
 * 字段类型接口（用于保存时的 fields 数组）
 */
export interface Field {
  key: string
  type: string
}

/**
 * 解析后的字段接口
 */
export interface ExtractedField {
  key: string
  type: string
  value: any
  path?: string
  regex?: string
}

/**
 * 项目类型定义
 */
export interface Project {
  id: number
  name: string
  description: string
  config_json: ProjectConfig
  created_by: number
  created_at: string
  updated_at: string
  is_deleted: boolean
  task_count?: number
  completed_count?: number
}

export interface ProjectConfig {
  version: string
  settings?: {
    showThumbnail?: boolean
    enableShortcut?: boolean
    autoSave?: boolean
    autoSaveInterval?: number
  }
  components: ComponentConfig[]
}

/**
 * 组件配置对象 - 包含所有业务配置字段
 */
export interface ComponentConfigData {
  field?: string  // 绑定的数据字段（图片路径、文本内容等）
  bbox_field?: string  // bbox 字段绑定（仅 image-viewer-bbox 使用）
  required?: boolean
  editable?: boolean  // 是否可编辑（默认为 true）
  visible_when?: {   // 条件显示配置
    field: string
    operator: '==' | '!=' | 'contains' | 'is_empty' | 'not_empty'
    value?: any
  }
  title?: string  // 组件标题
  options?: Array<{ value: string; label: string }>  // 选项配置（标签、单选等）
}

export interface ComponentConfig {
  id: string
  type: string  // 组件类型：image-viewer-bbox, image-viewer, text-field, tags, checkbox, radio-group, divider
  label?: string  // 显示标签
  // 画布布局和尺寸（保持平铺）
  x?: number  // X 位置（网格单位）
  y?: number  // Y 位置（网格单位）
  w?: number  // 宽度（网格单位，默认 4）
  h?: number  // 高度（网格单位，默认 1）
  // 业务配置统一放入 config 对象
  config: ComponentConfigData
  visible?: boolean
  attributes?: Record<string, any>
  validation?: {
    required?: boolean
    message?: string
  }
}

export interface ProjectCreate {
  name: string
  description?: string
  image_base_path?: string
  sample_json?: Record<string, any>
  fields?: Field[]  // 新增：字段数组
  config_json: ProjectConfig
}

export interface ProjectStatistics {
  total_tasks: number
  pending_tasks: number
  doing_tasks: number
  completed_tasks: number
  completion_rate: number
  daily_progress: Array<{
    date: string
    completed: number
  }>
}
