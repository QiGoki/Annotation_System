/**
 * 标注模块注册中心
 *
 * 组件市场的核心注册表
 * 每个组件按格式注册后才能在设计器中使用
 */
import type { ModuleDefinition } from '@/types/annotation-module'

// 引入已实现的组件
import ImageBBoxAnnotator from '@/components/annotation/ImageBBoxAnnotator.vue'
import ComponentTree from '@/components/annotation/ComponentTree.vue'
import AnnotationSidebar from '@/components/annotation/AnnotationSidebar.vue'

/**
 * 模块注册表
 *
 * 设计原则：
 * 1. schema.fields 声明组件需要哪些数据字段
 * 2. fieldMapping 提供智能推荐，根据数据自动匹配字段
 * 3. 用户在配置器中可以接受推荐或手动选择
 */
export const moduleRegistry: Record<string, ModuleDefinition> = {
  // === 图片拉框标注器 ===
  ImageBBoxAnnotator: {
    id: 'ImageBBoxAnnotator',
    name: '图片拉框标注器',
    icon: '🖼️',
    description: '显示图片并支持 bbox 标注',
    component: ImageBBoxAnnotator,
    schema: {
      fields: {
        imageUrl: { type: 'string', label: '图片路径', required: true },
        bboxes: { type: 'array', label: 'BBox 列表', required: false }
      }
    },
    fieldMapping: {
      imageUrl: (data) => data.image || data.images?.[0] || data.img,
      bboxes: (data) => {
        // 智能提取：可能是 components、elements、widgets 等
        const arr = data.components || data.elements || data.widgets
        if (!arr) return []

        const bboxes: any[] = []
        const extract = (items: any[]) => {
          for (const item of items) {
            if (item.bbox) bboxes.push({ path: [], bbox: item.bbox, type: item.type, text: item.text })
            if (item.children) extract(item.children)
          }
        }
        extract(arr)
        return bboxes
      }
    },
    defaultProps: {
      zoomable: true,
      bboxEditable: true,
      showAllBboxes: false
    }
  },

  // === 组件树 ===
  ComponentTree: {
    id: 'ComponentTree',
    name: '组件树',
    icon: '🌲',
    description: '以树形结构展示组件层级',
    component: ComponentTree,
    schema: {
      fields: {
        components: { type: 'array', label: '组件列表', required: true }
      }
    },
    fieldMapping: {
      components: (data) => data.components || data.elements || data.ui_components
    },
    defaultProps: {
      readonly: false
    }
  },

  // === 标注侧边栏（系统自动注入） ===
  AnnotationSidebar: {
    id: 'AnnotationSidebar',
    name: '标注侧边栏',
    icon: '📋',
    description: '显示任务列表和进度（系统自动注入）',
    component: AnnotationSidebar,
    schema: {
      fields: {
        items: { type: 'array', label: '条目列表', required: true }
      }
    },
    fieldMapping: {
      items: (data) => data  // 默认接收完整数据
    },
    defaultProps: {
      title: '标注任务'
    }
  }
}

/**
 * 获取所有可用模块（用于组件市场）
 */
export function getAllModules(): ModuleDefinition[] {
  return Object.values(moduleRegistry)
}

/**
 * 根据 ID 获取模块定义
 */
export function getModuleById(moduleId: string): ModuleDefinition | undefined {
  return moduleRegistry[moduleId]
}
