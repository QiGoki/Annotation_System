/**
 * 标注模块注册中心 v4
 *
 * 组件市场的核心注册表
 */
import type { ModuleDefinition, ConfigFieldSchema } from '@/types/annotation-module'

// 引入已实现的组件
import ImageBBoxAnnotator from '@/components/annotation/ImageBBoxAnnotator.vue'
import AnnotationSidebar from '@/components/annotation/AnnotationSidebar.vue'
import TextViewer from '@/components/annotation/TextViewer.vue'
import RadioSelector from '@/components/annotation/RadioSelector.vue'
import TextInput from '@/components/annotation/TextInput.vue'

// ==================== ConfigSchema 定义 ====================

/**
 * ImageBBoxAnnotator 配置 Schema
 */
const imageBBoxAnnotatorConfigSchema: Record<string, ConfigFieldSchema> = {
  title: { type: 'string', label: '标题', default: '图片标注器' },

  image: {
    type: 'group',
    label: '图片设置',
    fields: {
      field: { type: 'field-select', label: '图片字段', required: true },
      pathClean: {
        type: 'object',
        fields: {
          enabled: { type: 'boolean', label: '启用路径清洗' },
          prefix: { type: 'string', label: '要清除的前缀' }
        }
      }
    }
  },

  bboxSource: {
    type: 'group',
    label: 'BBox 数据源',
    fields: {
      mode: { type: 'select', label: '模式', options: ['list', 'string'] },
      dataPath: { type: 'field-select', label: '数据路径', showIf: { mode: 'list' } },
      bboxField: { type: 'string', label: 'BBox 字段名', showIf: { mode: 'list' }, default: 'bbox' },
      childrenField: { type: 'string', label: '子节点字段名', showIf: { mode: 'list' }, description: '树形结构时填写' },
      displayField: { type: 'string', label: '显示字段名', showIf: { mode: 'list' }, default: 'type', description: '树形结构时填写' },
      stringPath: { type: 'field-select', label: '字符串字段', showIf: { mode: 'string' } },
      extractRegex: { type: 'string', label: '提取正则', showIf: { mode: 'string' } }
    }
  },

  bboxProperties: {
    type: 'array',
    label: '属性定义',
    itemSchema: {
      name: { type: 'string', label: '属性标识' },
      sourceField: { type: 'string', label: '来源字段' },
      displayName: { type: 'string', label: '显示名称' },
      defaultValue: { type: 'string', label: '默认值' }
    }
  },

  representField: { type: 'string', label: '代表属性', default: 'type' },

  output: {
    type: 'group',
    label: '输出设置',
    fields: {
      fields: { type: 'string', label: '输出字段（逗号分隔）' }
    }
  }
}

/**
 * AnnotationSidebar 配置 Schema
 */
const annotationSidebarConfigSchema: Record<string, ConfigFieldSchema> = {
  title: { type: 'string', label: '标题', default: '标注任务' }
}

/**
 * TextViewer 配置 Schema
 */
const textViewerConfigSchema: Record<string, ConfigFieldSchema> = {
  title: { type: 'string', label: '标题', default: '文本查看' },
  field: { type: 'field-select', label: '绑定字段', required: true },
  multiline: { type: 'boolean', label: '多行显示', default: false }
}

/**
 * RadioSelector 配置 Schema
 */
const radioSelectorConfigSchema: Record<string, ConfigFieldSchema> = {
  title: { type: 'string', label: '标题', default: '单选' },
  field: { type: 'field-select', label: '绑定字段', required: true },
  multiSelect: { type: 'boolean', label: '允许多选', default: false },
  options: {
    type: 'array-string',
    label: '选项列表',
    description: '一行一个选项'
  },
  layout: {
    type: 'select',
    label: '布局方式',
    options: ['vertical', 'horizontal'],
    default: 'vertical'
  }
}

/**
 * TextInput 配置 Schema
 */
const textInputConfigSchema: Record<string, ConfigFieldSchema> = {
  title: { type: 'string', label: '标题', default: '文本输入' },
  mode: {
    type: 'select',
    label: '模式',
    options: ['绑定已有字段', '新增字段'],
    default: '绑定已有字段'
  },
  field: {
    type: 'field-select',
    label: '绑定字段',
    required: true,
    showIf: { mode: '绑定已有字段' }
  },
  newFieldName: {
    type: 'string',
    label: '新字段名称',
    required: true,
    description: '输入要新增的字段名',
    showIf: { mode: '新增字段' }
  },
  placeholder: { type: 'string', label: '占位文本', default: '' },
  required: { type: 'boolean', label: '必填', default: false },
  multiline: { type: 'boolean', label: '多行输入', default: false },
  maxLength: { type: 'number', label: '最大长度', default: 0 }
}

// ==================== 模块注册表 ====================

/**
 * 模块注册表
 */
export const moduleRegistry: Record<string, ModuleDefinition> = {
  // === 图片拉框标注器 ===
  ImageBBoxAnnotator: {
    id: 'ImageBBoxAnnotator',
    name: '图片拉框标注器',
    icon: '🖼️',
    description: '显示图片并支持 bbox 标注，支持扁平列表和树形结构',
    component: ImageBBoxAnnotator,

    configSchema: imageBBoxAnnotatorConfigSchema,

    defaultConfig: {
      title: '图片标注器',
      image: {
        field: 'image',
        pathClean: { enabled: false, prefix: '' }
      },
      bboxSource: {
        mode: 'list',
        dataPath: 'items',
        bboxField: 'bbox',
        childrenField: '',
        displayField: 'type'
      },
      bboxProperties: [
        { name: 'type', sourceField: 'type', displayName: '类型', defaultValue: 'unknown' },
        { name: 'text', sourceField: 'text', displayName: '文本', defaultValue: '' }
      ],
      representField: 'type',
      output: {
        fields: 'bbox,type,text'
      }
    }
  },

  // === 标注侧边栏（系统自动注入） ===
  AnnotationSidebar: {
    id: 'AnnotationSidebar',
    name: '标注侧边栏',
    icon: '📋',
    description: '显示任务列表和进度（系统自动注入）',
    component: AnnotationSidebar,

    configSchema: annotationSidebarConfigSchema,

    defaultConfig: {
      title: '标注任务'
    }
  },

  // === 文本查看器 ===
  TextViewer: {
    id: 'TextViewer',
    name: '文本查看器',
    icon: '📝',
    description: '显示文本内容，可直接编辑',
    component: TextViewer,

    configSchema: textViewerConfigSchema,

    defaultConfig: {
      title: '文本查看',
      field: '',
      multiline: false
    }
  },

  // === 单选组件 ===
  RadioSelector: {
    id: 'RadioSelector',
    name: '单选组件',
    icon: '🔘',
    description: '单选或多选选项列表，支持横向/纵向布局',
    component: RadioSelector,

    configSchema: radioSelectorConfigSchema,

    defaultConfig: {
      title: '单选',
      field: '',
      multiSelect: false,
      options: ['选项1', '选项2', '选项3'],
      layout: 'vertical'
    }
  },

  // === 文本输入 ===
  TextInput: {
    id: 'TextInput',
    name: '文本输入',
    icon: '✏️',
    description: '自定义标题+输入框，支持新增字段',
    component: TextInput,

    configSchema: textInputConfigSchema,

    defaultConfig: {
      title: '文本输入',
      mode: '绑定已有字段',
      field: '',
      newFieldName: '',
      placeholder: '',
      required: false,
      multiline: false,
      maxLength: 0
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