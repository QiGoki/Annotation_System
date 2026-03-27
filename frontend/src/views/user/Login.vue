<script setup lang="ts">
/**
 * 登录页面
 */
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

interface LoginForm {
  username: string
  password: string
}

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = ref<LoginForm>({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应在 3-50 个字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await userStore.login(form.value)
      ElMessage.success('登录成功')

      // 跳转到重定向页面或首页
      const redirect = route.query.redirect as string
      if (redirect) {
        router.push(redirect)
      } else {
        router.push('/projects')
      }
    } catch (e: any) {
      // 解析后端返回的详细错误信息
      let errorMsg = '登录失败'
      if (e.response?.data?.detail) {
        const detail = e.response.data.detail
        if (typeof detail === 'string') {
          errorMsg = detail
        } else if (Array.isArray(detail)) {
          // Pydantic 验证错误数组
          errorMsg = detail.map((err: any) => {
            const field = err.loc?.join('.') || '输入'
            const msg = err.msg || '验证失败'
            return `${field}: ${msg}`
          }).join('; ')
        }
      }
      ElMessage.error(errorMsg)
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>标注平台登录</h2>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-tip">
        <p>默认管理员账号：admin / admin123</p>
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f5f7fa;
}

.login-card {
  width: 420px;

  h2 {
    text-align: center;
    margin: 0;
    color: #333;
    font-size: 24px;
    font-weight: 600;
  }
}

.login-tip {
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;

  p {
    margin: 0;
    color: #666;
    font-size: 12px;
    text-align: center;
  }
}
</style>
