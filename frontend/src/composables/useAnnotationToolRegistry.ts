/**
 * 标注工具注册中心
 * 定义所有可用的标注工具及其配置
 */
import type { AnnotationTool } from '@/types/annotation-tool'

// 工具注册表
const toolRegistry: Record<string, AnnotationTool> = {
  // === 空间标注工具 ===
  'image_bbox': {
    id: 'image_bbox',
    name: '图片拉框标注器',
    icon: '🖼️',
    description: '用于图片上的矩形框标注',
    category: 'spatial',
    propsSchema: {
      showBBox: {
        type: 'boolean',
        label: '显示边框',
        default: true,
        description: '是否显示已标注的边框'
      },
      bboxEditable: {
        type: 'boolean',
        label: '可编辑',
        default: true,
        description: '是否允许拖拽调整边框'
      },
      zoomable: {
        type: 'boolean',
        label: '可缩放',
        default: true,
        description: '是否允许缩放图片'
      }
    },
    defaultProps: {
      showBBox: true,
      bboxEditable: true,
      zoomable: true
    }
  },

  'component_tree': {
    id: 'component_tree',
    name: '组件树',
    icon: '🌲',
    description: '以树形结构展示和选择组件',
    category: 'structural',
    propsSchema: {
      expandLevel: {
        type: 'number',
        label: '默认展开层级',
        default: 2,
        description: '初始展开的树层级深度'
      },
      highlightOnHover: {
        type: 'boolean',
        label: '悬停高亮',
        default: true,
        description: '鼠标悬停时高亮对应元素'
      },
      showActions: {
        type: 'boolean',
        label: '显示操作按钮',
        default: true,
        description: '是否显示添加/删除/移动按钮'
      }
    },
    defaultProps: {
      expandLevel: 2,
      highlightOnHover: true,
      showActions: true
    }
  },

  // === 文本标注工具 ===
  'text_editor': {
    id: 'text_editor',
    name: '文本编辑器',
    icon: '✏️',
    description: '用于文本内容的标注和编辑',
    category: 'text',
    propsSchema: {
      multiline: {
        type: 'boolean',
        label: '多行编辑',
        default: true,
        description: '是否允许多行文本输入'
      },
      placeholder: {
        type: 'string',
        label: '占位符',
        default: '请输入标注内容',
        description: '输入框占位文本'
      },
      maxLength: {
        type: 'number',
        label: '最大长度',
        default: 1000,
        description: '允许输入的最大字符数'
      }
    },
    defaultProps: {
      multiline: true,
      placeholder: '请输入标注内容',
      maxLength: 1000
    }
  },

  'text_ner': {
    id: 'text_ner',
    name: '文本实体标注',
    icon: '🏷️',
    description: '在文本上选择并标注实体',
    category: 'text',
    propsSchema: {
      entityTypes: {
        type: 'array',
        label: '实体类型',
        default: ['人名', '地名', '组织', '时间', '其他'],
        description: '可选的实体类型列表'
      },
      allowOverlap: {
        type: 'boolean',
        label: '允许重叠',
        default: false,
        description: '是否允许实体标注重叠'
      }
    },
    defaultProps: {
      entityTypes: ['人名', '地名', '组织', '时间', '其他'],
      allowOverlap: false
    }
  },

  // === 分类工具 ===
  'classification': {
    id: 'classification',
    name: '分类选择器',
    icon: '📋',
    description: '从预定义类别中选择一个标签',
    category: 'classification',
    propsSchema: {
      options: {
        type: 'select',
        label: '选项配置',
        required: true,
        options: [
          { label: '单选', value: 'single' },
          { label: '多选', value: 'multiple' }
        ],
        default: 'single',
        description: '选择模式配置'
      },
      categories: {
        type: 'array',
        label: '分类列表',
        default: ['正面', '负面', '中性'],
        description: '可选的分类标签'
      }
    },
    defaultProps: {
      options: 'single',
      categories: ['正面', '负面', '中性']
    }
  },

  'tag_cloud': {
    id: 'tag_cloud',
    name: '标签云',
    icon: '☁️',
    description: '从标签云中选择多个标签',
    category: 'classification',
    propsSchema: {
      tags: {
        type: 'array',
        label: '标签列表',
        default: ['重要', '紧急', '待处理', '已完成'],
        description: '可选的标签列表'
      },
      maxSelection: {
        type: 'number',
        label: '最大选择数',
        default: 5,
        description: '最多可选择的标签数量'
      }
    },
    defaultProps: {
      tags: ['重要', '紧急', '待处理', '已完成'],
      maxSelection: 5
    }
  },

  // === 结构化工具 ===
  'json_tree': {
    id: 'json_tree',
    name: 'JSON 树查看器',
    icon: '📋',
    description: '以树形结构展示 JSON 数据',
    category: 'structural',
    propsSchema: {
      expandLevel: {
        type: 'number',
        label: '默认展开层级',
        default: 1,
        description: '初始展开的树层级深度'
      },
      showTypes: {
        type: 'boolean',
        label: '显示类型',
        default: true,
        description: '是否显示字段类型图标'
      },
      editable: {
        type: 'boolean',
        label: '可编辑',
        default: false,
        description: '是否允许编辑 JSON 值'
      }
    },
    defaultProps: {
      expandLevel: 1,
      showTypes: true,
      editable: false
    }
  },

  'table_viewer': {
    id: 'table_viewer',
    name: '表格查看器',
    icon: '📊',
    description: '以表格形式展示结构化数据',
    category: 'structural',
    propsSchema: {
      columns: {
        type: 'array',
        label: '列配置',
        default: [],
        description: '表格列定义'
      },
      striped: {
        type: 'boolean',
        label: '斑马纹',
        default: true,
        description: '是否显示斑马纹样式'
      },
      border: {
        type: 'boolean',
        label: '边框',
        default: false,
        description: '是否显示边框'
      }
    },
    defaultProps: {
      columns: [],
      striped: true,
      border: false
    }
  }
}

/**
 * 获取所有可用工具
 */
export function getAllTools(): AnnotationTool[] {
  return Object.values(toolRegistry)
}

/**
 * 按类别获取工具
 */
export function getToolsByCategory(category: AnnotationTool['category']): AnnotationTool[] {
  return Object.values(toolRegistry).filter(tool => tool.category === category)
}

/**
 * 根据 ID 获取工具定义
 */
export function getToolById(toolId: string): AnnotationTool | undefined {
  return toolRegistry[toolId]
}

/**
 * 创建工具实例
 */
export function createToolInstance(
  toolId: string,
  overrides?: Partial<Omit<AnnotationTool, 'id' | 'toolId'>>
): { id: string; toolId: string; name: string; props: Record<string, any> } | null {
  const tool = toolRegistry[toolId]
  if (!tool) return null

  return {
    id: `${toolId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    toolId: tool.id,
    name: tool.name,
    props: { ...tool.defaultProps, ...overrides }
  }
}

/**
 * 注册新工具
 */
export function registerTool(tool: AnnotationTool): void {
  toolRegistry[tool.id] = tool
}

/**
 * 获取工具类别列表
 */
export function getToolCategories(): { id: string; name: string }[] {
  const categoryNames: Record<string, string> = {
    spatial: '空间标注',
    text: '文本标注',
    classification: '分类标注',
    structural: '结构查看'
  }

  return Object.keys(categoryNames).map(id => ({
    id,
    name: categoryNames[id]
  }))
}
