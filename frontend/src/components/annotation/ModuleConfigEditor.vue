<script setup lang="ts">
/**
 * 模块配置编辑器
 *
 * 根据 configSchema 动态渲染配置表单
 */
import { computed, watch } from 'vue'
import type { ConfigFieldSchema, ParsedField } from '@/types/annotation-module'
import { getModuleById } from '@/composables/useAnnotationModuleRegistry'

interface Props {
  moduleType: string
  config: any
  parsedFields?: ParsedField[]
}

const props = withDefaults(defineProps<Props>(), {
  parsedFields: () => []
})

const emit = defineEmits<{
  'update:config': [config: any]
}>()

// 获取模块定义
const moduleDef = computed(() => getModuleById(props.moduleType))
const configSchema = computed(() => moduleDef.value?.configSchema || {})

// 本地配置（深拷贝避免直接修改 prop）
const localConfig = computed({
  get: () => props.config || {},
  set: (val) => emit('update:config', val)
})

// 初始化默认值
watch(() => props.moduleType, () => {
  if (!props.config && moduleDef.value?.defaultConfig) {
    emit('update:config', JSON.parse(JSON.stringify(moduleDef.value.defaultConfig)))
  }
}, { immediate: true })

// 更新配置字段
const updateField = (path: string, value: any) => {
  const newConfig = JSON.parse(JSON.stringify(localConfig.value))
  const parts = path.split('.')

  let current: any = newConfig
  for (let i = 0; i < parts.length - 1; i++) {
    if (!current[parts[i]]) {
      current[parts[i]] = {}
    }
    current = current[parts[i]]
  }

  current[parts[parts.length - 1]] = value
  emit('update:config', newConfig)
}

// 获取嵌套值
const getValue = (path: string): any => {
  const parts = path.split('.')
  let current: any = localConfig.value

  for (const part of parts) {
    if (current === null || current === undefined) return undefined
    current = current[part]
  }

  return current
}

// 判断字段是否显示（pathPrefix 用于 showIf 条件检查）
const shouldShow = (schema: ConfigFieldSchema, pathPrefix?: string): boolean => {
  if (!('showIf' in schema) || !schema.showIf) return true

  for (const [field, expectedValue] of Object.entries(schema.showIf)) {
    const fullPath = pathPrefix ? `${pathPrefix}.${field}` : field
    if (getValue(fullPath) !== expectedValue) {
      return false
    }
  }

  return true
}

// 渲染字段类型
const getFieldType = (schema: ConfigFieldSchema): string => {
  return schema.type
}

// 数组操作
const addArrayItem = (path: string, itemSchema: Record<string, ConfigFieldSchema>) => {
  const arr = getValue(path) || []
  const newItem: any = {}

  // 初始化默认值
  for (const [key, schema] of Object.entries(itemSchema)) {
    if ('default' in schema) {
      newItem[key] = schema.default
    }
  }

  updateField(path, [...arr, newItem])
}

const removeArrayItem = (path: string, index: number) => {
  const arr = getValue(path) || []
  updateField(path, arr.filter((_: any, i: number) => i !== index))
}

const updateArrayItem = (path: string, index: number, field: string, value: any) => {
  const arr = getValue(path) || []
  const newArr = [...arr]
  newArr[index] = { ...newArr[index], [field]: value }
  updateField(path, newArr)
}

// 字符串数组操作（array-string 类型）
const addStringArrayItem = (path: string) => {
  const arr = getValue(path) || []
  updateField(path, [...arr, ''])
}

const removeStringArrayItem = (path: string, index: number) => {
  const arr = getValue(path) || []
  updateField(path, arr.filter((_: any, i: number) => i !== index))
}

const updateStringArrayItem = (path: string, index: number, value: string) => {
  const arr = getValue(path) || []
  const newArr = [...arr]
  newArr[index] = value
  updateField(path, newArr)
}

// 解析字符串数组选项（支持 label:value 格式）
const parseOptionsText = (text: string): string[] => {
  return text.split('\n').map(line => line.trim()).filter(line => line.length > 0)
}

const getOptionsText = (path: string): string => {
  const arr = getValue(path) || []
  return arr.join('\n')
}

const updateOptionsFromText = (path: string, text: string) => {
  updateField(path, parseOptionsText(text))
}
</script>

<template>
  <div class="module-config-editor">
    <div v-if="!moduleDef" class="empty-state">
      请选择一个模块
    </div>

    <template v-else>
      <!-- 遍历 configSchema 渲染表单 -->
      <template v-for="(schema, key) in configSchema" :key="key">
        <!-- 分组类型 -->
        <template v-if="schema.type === 'group'">
          <div class="config-group">
            <div class="group-title">{{ schema.label }}</div>
            <div class="group-fields">
              <template v-for="(subSchema, subKey) in schema.fields" :key="subKey">
                <div class="config-field" v-if="shouldShow(subSchema, key as string)">
                  <label class="field-label">
                    {{ subSchema.label }}
                    <span v-if="'required' in subSchema && subSchema.required" class="required">*</span>
                  </label>

                  <!-- 字段选择 -->
                  <select
                    v-if="subSchema.type === 'field-select'"
                    class="form-input"
                    :value="getValue(`${key}.${subKey}`)"
                    @change="updateField(`${key}.${subKey}`, ($event.target as HTMLSelectElement).value)"
                  >
                    <option value="">选择字段</option>
                    <option v-for="field in parsedFields" :key="field.path" :value="field.path">
                      {{ field.path }} ({{ field.type }})
                    </option>
                  </select>

                  <!-- 字符串输入 -->
                  <input
                    v-else-if="subSchema.type === 'string'"
                    type="text"
                    class="form-input"
                    :value="getValue(`${key}.${subKey}`)"
                    @input="updateField(`${key}.${subKey}`, ($event.target as HTMLInputElement).value)"
                  />

                  <!-- 布尔值 -->
                  <label v-else-if="subSchema.type === 'boolean'" class="checkbox-label">
                    <input
                      type="checkbox"
                      :checked="getValue(`${key}.${subKey}`)"
                      @change="updateField(`${key}.${subKey}`, ($event.target as HTMLInputElement).checked)"
                    />
                    <span>启用</span>
                  </label>

                  <!-- 选择框 -->
                  <select
                    v-else-if="subSchema.type === 'select'"
                    class="form-input"
                    :value="getValue(`${key}.${subKey}`)"
                    @change="updateField(`${key}.${subKey}`, ($event.target as HTMLSelectElement).value)"
                  >
                    <option v-for="opt in subSchema.options" :key="opt" :value="opt">{{ opt }}</option>
                  </select>

                  <!-- 对象类型 -->
                  <template v-else-if="subSchema.type === 'object'">
                    <div class="object-fields">
                      <template v-for="(objSchema, objKey) in subSchema.fields" :key="objKey">
                        <div class="config-field-inline">
                          <label>{{ objSchema.label }}</label>
                          <input
                            v-if="objSchema.type === 'string'"
                            type="text"
                            class="form-input form-input-sm"
                            :value="getValue(`${key}.${subKey}.${objKey}`)"
                            @input="updateField(`${key}.${subKey}.${objKey}`, ($event.target as HTMLInputElement).value)"
                          />
                          <label v-else-if="objSchema.type === 'boolean'" class="checkbox-label">
                            <input
                              type="checkbox"
                              :checked="getValue(`${key}.${subKey}.${objKey}`)"
                              @change="updateField(`${key}.${subKey}.${objKey}`, ($event.target as HTMLInputElement).checked)"
                            />
                          </label>
                        </div>
                      </template>
                    </div>
                  </template>
                </div>
              </template>
            </div>
          </div>
        </template>

        <!-- 数组类型 -->
        <template v-else-if="schema.type === 'array'">
          <div class="config-group">
            <div class="group-header">
              <span class="group-title">{{ schema.label }}</span>
              <button class="btn btn-sm btn-primary" @click="addArrayItem(key as string, schema.itemSchema)">
                + 添加
              </button>
            </div>

            <div class="array-items">
              <div v-for="(item, index) in getValue(key as string) || []" :key="index" class="array-item">
                <div class="array-item-header">
                  <span>#{{ index + 1 }}</span>
                  <button class="btn btn-sm btn-danger" @click="removeArrayItem(key as string, index)">
                    删除
                  </button>
                </div>

                <div class="array-item-fields">
                  <template v-for="(itemSchema, itemKey) in schema.itemSchema" :key="itemKey">
                    <div class="config-field-inline">
                      <label>{{ itemSchema.label }}</label>

                      <!-- 字段选择 -->
                      <select
                        v-if="itemSchema.type === 'field-select'"
                        class="form-input form-input-sm"
                        :value="item[itemKey]"
                        @change="updateArrayItem(key as string, index, itemKey as string, ($event.target as HTMLSelectElement).value)"
                      >
                        <option value="">选择字段</option>
                        <option v-for="field in parsedFields" :key="field.path" :value="field.path">
                          {{ field.path }}
                        </option>
                      </select>

                      <!-- 字符串输入 -->
                      <input
                        v-else-if="itemSchema.type === 'string'"
                        type="text"
                        class="form-input form-input-sm"
                        :value="item[itemKey]"
                        @input="updateArrayItem(key as string, index, itemKey as string, ($event.target as HTMLInputElement).value)"
                      />
                    </div>
                  </template>
                </div>
              </div>

              <div v-if="(getValue(key as string) || []).length === 0" class="empty-array">
                暂无配置，点击上方按钮添加
              </div>
            </div>
          </div>
        </template>

        <!-- 基础类型（非分组、非数组） -->
        <template v-else>
          <div class="config-field" v-if="shouldShow(schema)">
            <label class="field-label">
              {{ schema.label }}
              <span v-if="'required' in schema && schema.required" class="required">*</span>
            </label>

            <!-- 字段选择 -->
            <select
              v-if="schema.type === 'field-select'"
              class="form-input"
              :value="getValue(key as string)"
              @change="updateField(key as string, ($event.target as HTMLSelectElement).value)"
            >
              <option value="">选择字段</option>
              <option v-for="field in parsedFields" :key="field.path" :value="field.path">
                {{ field.path }} ({{ field.type }})
              </option>
            </select>

            <!-- 字符串输入 -->
            <input
              v-else-if="schema.type === 'string'"
              type="text"
              class="form-input"
              :value="getValue(key as string)"
              @input="updateField(key as string, ($event.target as HTMLInputElement).value)"
            />

            <!-- 布尔值 -->
            <label v-else-if="schema.type === 'boolean'" class="checkbox-label">
              <input
                type="checkbox"
                :checked="getValue(key as string)"
                @change="updateField(key as string, ($event.target as HTMLInputElement).checked)"
              />
              <span>启用</span>
            </label>

            <!-- 选择框 -->
            <select
              v-else-if="schema.type === 'select'"
              class="form-input"
              :value="getValue(key as string)"
              @change="updateField(key as string, ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="opt in schema.options" :key="opt" :value="opt">{{ opt }}</option>
            </select>

            <!-- 数字输入 -->
            <input
              v-else-if="schema.type === 'number'"
              type="number"
              class="form-input"
              :value="getValue(key as string)"
              @input="updateField(key as string, parseInt(($event.target as HTMLInputElement).value) || 0)"
            />

            <!-- 字符串数组（textarea） -->
            <textarea
              v-else-if="schema.type === 'array-string'"
              class="form-input form-textarea"
              rows="4"
              :value="getOptionsText(key as string)"
              @input="updateOptionsFromText(key as string, ($event.target as HTMLTextAreaElement).value)"
              :placeholder="schema.description || '一行一个选项'"
            />
          </div>
        </template>
      </template>
    </template>
  </div>
</template>

<style scoped>
.module-config-editor {
  padding: 12px;
}

.empty-state {
  text-align: center;
  color: #9CA3AF;
  padding: 40px;
}

.config-group {
  margin-bottom: 16px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  overflow: hidden;
}

.group-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  padding: 8px 12px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.group-fields {
  padding: 12px;
}

.config-field {
  margin-bottom: 12px;
}

.config-field:last-child {
  margin-bottom: 0;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 4px;
}

.required {
  color: #EF4444;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 13px;
  transition: border-color 0.15s;
}

.form-input:focus {
  outline: none;
  border-color: #165DFF;
}

.form-input-sm {
  padding: 6px 8px;
  font-size: 12px;
}

.form-textarea {
  font-family: inherit;
  resize: vertical;
  min-height: 60px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input {
  width: 16px;
  height: 16px;
}

.object-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-field-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-field-inline label {
  flex-shrink: 0;
  font-size: 12px;
  color: #6B7280;
  min-width: 80px;
}

.config-field-inline .form-input {
  flex: 1;
}

.array-items {
  padding: 12px;
}

.array-item {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.array-item:last-child {
  margin-bottom: 0;
}

.array-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
}

.array-item-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-array {
  text-align: center;
  color: #9CA3AF;
  font-size: 12px;
  padding: 16px;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 11px;
}

.btn-primary {
  background: #165DFF;
  color: white;
}

.btn-primary:hover {
  background: #0E42D2;
}

.btn-danger {
  background: #FEE2E2;
  color: #EF4444;
}

.btn-danger:hover {
  background: #FECACA;
}
</style>