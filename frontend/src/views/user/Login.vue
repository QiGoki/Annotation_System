<script setup lang="ts">
/**
 * 登录页面 - StepFun风格
 */
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

interface LoginForm {
  username: string
  password: string
}

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const form = ref<LoginForm>({
  username: '',
  password: '',
})

const errors = ref<{ username?: string; password?: string }>({})

const validate = () => {
  errors.value = {}
  let valid = true

  if (!form.value.username) {
    errors.value.username = '请输入用户名'
    valid = false
  } else if (form.value.username.length < 3 || form.value.username.length > 50) {
    errors.value.username = '用户名长度应在 3-50 个字符之间'
    valid = false
  }

  if (!form.value.password) {
    errors.value.password = '请输入密码'
    valid = false
  } else if (form.value.password.length < 6) {
    errors.value.password = '密码长度至少为 6 个字符'
    valid = false
  }

  return valid
}

const handleLogin = async () => {
  if (!validate()) return

  loading.value = true
  try {
    await userStore.login(form.value)
    const redirect = route.query.redirect as string
    router.push(redirect || '/projects')
  } catch (e: any) {
    let errorMsg = '登录失败'
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (typeof detail === 'string') {
        errorMsg = detail
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map((err: any) => err.msg || '验证失败').join('; ')
      }
    }
    alert(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-header">
        <div class="logo">
          <div class="logo-icon">S</div>
          <span class="logo-text">标注平台</span>
        </div>
        <h1>欢迎登录</h1>
        <p class="subtitle">多模态混合标注低代码平台</p>
      </div>

      <!-- 表单 -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input
            v-model="form.username"
            type="text"
            class="form-input form-input-lg"
            :class="{ 'form-input-error': errors.username }"
            placeholder="请输入用户名"
          />
          <span v-if="errors.username" class="form-error">{{ errors.username }}</span>
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="form-input form-input-lg"
            :class="{ 'form-input-error': errors.password }"
            placeholder="请输入密码"
          />
          <span v-if="errors.password" class="form-error">{{ errors.password }}</span>
        </div>

        <button type="submit" class="btn btn-primary btn-block btn-lg" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <!-- 提示 -->
      <div class="login-tip">
        <p>默认管理员账号：admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #F9FAFB 0%, #F0F5FF 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: #165DFF;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: 700;
}

.logo-text {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
}

.login-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #6B7280;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-input-lg {
  padding: 14px 16px;
  font-size: 15px;
}

.form-input-error {
  border-color: #EF4444;
}

.form-input-error:focus {
  border-color: #EF4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.form-error {
  font-size: 12px;
  color: #EF4444;
  margin-top: 4px;
}

.btn-block {
  width: 100%;
}

.login-tip {
  margin-top: 24px;
  padding: 16px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
}

.login-tip p {
  margin: 0;
  color: #6B7280;
  font-size: 13px;
  text-align: center;
}
</style>