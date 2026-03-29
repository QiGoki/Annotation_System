<script setup lang="ts">
/**
 * 创建用户页面 - StepFun风格
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createUser } from '@/api/user'

const router = useRouter()
const loading = ref(false)

const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'annotator',
  is_active: true
})

const errors = ref<{ username?: string; password?: string; confirmPassword?: string }>({})

const validate = () => {
  errors.value = {}
  let valid = true

  if (!formData.username) {
    errors.value.username = '请输入用户名'
    valid = false
  } else if (formData.username.length < 3 || formData.username.length > 20) {
    errors.value.username = '用户名长度应在 3-20 个字符之间'
    valid = false
  }

  if (!formData.password) {
    errors.value.password = '请输入密码'
    valid = false
  } else if (formData.password.length < 6) {
    errors.value.password = '密码长度至少 6 位'
    valid = false
  }

  if (!formData.confirmPassword) {
    errors.value.confirmPassword = '请确认密码'
    valid = false
  } else if (formData.confirmPassword !== formData.password) {
    errors.value.confirmPassword = '两次输入的密码不一致'
    valid = false
  }

  return valid
}

const handleSubmit = async () => {
  if (!validate()) return

  loading.value = true
  try {
    await createUser({
      username: formData.username,
      password: formData.password,
      role: formData.role,
      is_active: formData.is_active
    })
    alert('创建成功')
    router.push('/users')
  } catch (e: any) {
    let errorMsg = '创建失败'
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (typeof detail === 'string') {
        errorMsg = detail
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join('; ')
      }
    }
    alert(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <!-- 顶部 Header -->
    <div class="page-header-bar">
      <div class="header-info">
        <h1 class="header-title">创建用户</h1>
        <span class="header-subtitle">添加新的平台用户</span>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="router.push('/users')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          返回
        </button>
        <button class="btn btn-primary" :disabled="loading" @click="handleSubmit">
          <svg v-if="!loading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          创建用户
        </button>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="page-body">
      <div class="form-card">
        <h3 class="form-title">用户信息</h3>
        <form class="form">
          <div class="form-group">
            <label class="form-label required">用户名</label>
            <input
              v-model="formData.username"
              type="text"
              class="form-input"
              :class="{ 'form-input-error': errors.username }"
              placeholder="请输入用户名（3-20 个字符）"
              maxlength="20"
            />
            <span v-if="errors.username" class="form-error">{{ errors.username }}</span>
          </div>

          <div class="form-group">
            <label class="form-label required">密码</label>
            <input
              v-model="formData.password"
              type="password"
              class="form-input"
              :class="{ 'form-input-error': errors.password }"
              placeholder="请输入密码（至少 6 位）"
            />
            <span v-if="errors.password" class="form-error">{{ errors.password }}</span>
          </div>

          <div class="form-group">
            <label class="form-label required">确认密码</label>
            <input
              v-model="formData.confirmPassword"
              type="password"
              class="form-input"
              :class="{ 'form-input-error': errors.confirmPassword }"
              placeholder="请再次输入密码"
            />
            <span v-if="errors.confirmPassword" class="form-error">{{ errors.confirmPassword }}</span>
          </div>

          <div class="form-group">
            <label class="form-label required">角色</label>
            <div class="radio-group">
              <label class="radio">
                <input type="radio" v-model="formData.role" value="annotator" />
                <span class="radio-label">标注员</span>
              </label>
              <label class="radio">
                <input type="radio" v-model="formData.role" value="admin" />
                <span class="radio-label">管理员</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">启用状态</label>
            <div class="switch-group">
              <label class="switch">
                <input type="checkbox" v-model="formData.is_active" />
                <span class="switch-track">
                  <span class="switch-thumb"></span>
                </span>
              </label>
              <span class="switch-label">{{ formData.is_active ? '启用' : '禁用' }}</span>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.page-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #E5E7EB;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #9CA3AF;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.page-body {
  flex: 1;
  padding: 24px;
  overflow: auto;
}

.form-card {
  max-width: 480px;
  margin: 0 auto;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.form-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 20px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-label.required::after {
  content: ' *';
  color: #EF4444;
}

.form-error {
  font-size: 12px;
  color: #EF4444;
  margin-top: 4px;
}

.form-input-error {
  border-color: #EF4444;
}

.radio-group {
  display: flex;
  gap: 20px;
}

.radio {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio input {
  width: 18px;
  height: 18px;
  accent-color: #165DFF;
}

.switch-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.switch {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.switch input {
  display: none;
}

.switch-track {
  width: 44px;
  height: 24px;
  background: #E5E7EB;
  border-radius: 12px;
  position: relative;
  transition: background-color 0.2s ease;
}

.switch input:checked + .switch-track {
  background: #165DFF;
}

.switch-thumb {
  position: absolute;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 10px;
  top: 2px;
  left: 2px;
  transition: transform 0.2s ease;
}

.switch input:checked + .switch-track .switch-thumb {
  transform: translateX(20px);
}

.switch-label {
  font-size: 14px;
  color: #111827;
}
</style>