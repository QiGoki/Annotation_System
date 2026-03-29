/**
 * 数据源解析工具
 *
 * 用于：
 * 1. 上传示例 JSON → 自动提取字段
 * 2. JSONPath 解析
 */
import type { ParsedField, CustomFieldRule } from '@/types/annotation-module'

/**
 * 提取 JSON 数据中的所有字段路径
 *
 * 规则：
 * - 字段值 = 列表：
 *   - 列表中没有对象 → 保留该字段
 *   - 列表中有对象 → 保留数组路径 + 展开第一个对象供参考
 * - 字段值 = 对象 → 继续递归展开
 * - 字段值 = 基本类型 → 直接保留
 */
export function extractFields(data: any, prefix = ''): ParsedField[] {
  const fields: ParsedField[] = []

  for (const [key, val] of Object.entries(data)) {
    const fullPath = prefix ? `${prefix}.${key}` : key

    if (val === null || val === undefined) continue

    if (Array.isArray(val)) {
      // 检查数组中是否有对象
      const hasObject = val.some(item => typeof item === 'object' && item !== null)

      if (hasObject) {
        // 数组中有对象 → 保留数组路径本身
        const firstObject = val.find(item => typeof item === 'object' && item !== null)
        fields.push({
          path: fullPath,
          type: 'array',
          length: val.length,
          preview: firstObject ? `包含 ${Object.keys(firstObject).join(', ')} 等字段` : undefined
        })

        // 同时展开第一个对象供参考（缩进显示）
        if (firstObject) {
          const subFields = extractFields(firstObject, `${fullPath}[0]`)
          fields.push(...subFields.map(f => ({
            ...f,
            preview: `└─ ${f.preview || f.type}`  // 添加缩进标记表示是子字段
          })))
        }
      } else {
        // 数组中没有对象 → 保留该字段
        fields.push({
          path: fullPath,
          type: 'array',
          length: val.length,
          sampleValue: val[0]
        })
      }
    } else if (typeof val === 'object') {
      // 对象 → 继续递归展开
      fields.push(...extractFields(val, fullPath))
    } else {
      // 基本类型 → 直接保留
      fields.push({
        path: fullPath,
        type: typeof val,
        sampleValue: val
      })
    }
  }

  return fields
}

/**
 * 根据 JSONPath 解析数据
 *
 * 支持路径格式：
 * - 'image' → data.image
 * - 'components[0].bbox' → data.components[0].bbox
 */
export function resolveFieldBinding(data: any, bindingPath: string): any {
  if (!bindingPath) return undefined

  // 解析 JSONPath segments
  const segments = bindingPath.match(/[^.[\]]+|\[\d+\]/g) || []
  let result = data

  for (const seg of segments) {
    if (seg.startsWith('[') && seg.endsWith(']')) {
      result = result[parseInt(seg.slice(1, -1))]
    } else {
      result = result[seg]
    }
    if (result === undefined || result === null) return undefined
  }

  return result
}

/**
 * 应用自定义字段规则
 *
 * @param data 原始数据
 * @param rules 自定义规则列表
 * @returns 解析后的自定义字段
 */
export function applyCustomFieldRules(data: any, rules: CustomFieldRule[]): Record<string, any> {
  const result: Record<string, any> = {}

  for (const rule of rules) {
    if (rule.ruleType === 'path' && rule.path) {
      // JSONPath 解析
      result[rule.name] = resolveFieldBinding(data, rule.path)
    } else if (rule.ruleType === 'regex' && rule.regex && rule.regexSource) {
      // 正则表达式解析
      const sourceValue = resolveFieldBinding(data, rule.regexSource)
      if (sourceValue && typeof sourceValue === 'string') {
        try {
          const regex = new RegExp(rule.regex)
          const match = sourceValue.match(regex)
          if (match) {
            // 如果有捕获组，返回捕获组；否则返回整个匹配
            result[rule.name] = match[1] || match[0]
          }
        } catch (e) {
          console.error('正则表达式解析失败:', rule.regex, e)
        }
      }
    }
  }

  return result
}

/**
 * 提取字段（增强版，支持自定义规则）
 */
export function extractFieldsWithRules(data: any, rules?: CustomFieldRule[]): ParsedField[] {
  const fields = extractFields(data)

  if (rules && rules.length > 0) {
    const customFields = applyCustomFieldRules(data, rules)
    for (const [name, value] of Object.entries(customFields)) {
      fields.push({
        path: `custom:${name}`,
        type: typeof value,
        sampleValue: value
      })
    }
  }

  return fields
}