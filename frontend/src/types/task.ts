/**
 * 任务类型定义
 */
import type { ProjectConfig } from './project'

export interface Task {
  id: number
  project_id: number
  project_name?: string
  data_source: DataSource
  status: 'pending' | 'doing' | 'completed'
  assigned_to: number | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface DataSource {
  type: 'image' | 'text'
  url?: string
  content?: string
  width?: number
  height?: number
  filename?: string
}

export interface TaskWithAnnotation extends Task {
  project_name: string
  project_config: ProjectConfig
  annotation?: {
    id: number
    result_json: Record<string, any>
    created_at: string
  } | null
}

export interface TaskAssign {
  assigned_to: number
}

export interface TaskStatusUpdate {
  status: 'pending' | 'doing' | 'completed'
}

export interface Rect {
  x: number
  y: number
  width: number
  height: number
  label?: string
  id?: string
}
