/**
 * Vitest 测试设置文件
 */
import { config } from '@vue/test-utils'
import { vi, expect } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'

// 添加 jest-dom 匹配器
expect.extend(matchers)

// 全局组件配置 - stub Element Plus 组件
config.global.stubs = {
  RouterLink: false,
  Transition: false,
  TransitionGroup: false,
  // Element Plus 组件
  ElButton: true,
  ElInput: true,
  ElForm: true,
  ElFormItem: true,
  ElRadio: true,
  ElRadioGroup: true,
  ElSelect: true,
  ElOption: true,
  ElTag: true,
  ElScrollbar: true,
  ElEmpty: true,
  ElAlert: true,
  ElSwitch: true,
  ElCard: true,
  ElTable: true,
  ElTableColumn: true,
  ElProgress: true,
  ElIcon: true,
  ElRow: true,
  ElCol: true,
}

// 模拟 window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// 模拟 Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
  ElMessageBox: {
    confirm: vi.fn(),
    alert: vi.fn(),
  },
}))
