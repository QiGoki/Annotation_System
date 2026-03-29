/**
 * 标注工具类型定义
 */

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
}