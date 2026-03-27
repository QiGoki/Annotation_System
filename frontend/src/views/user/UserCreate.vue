<template>
  <div class="user-create">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <h2>创建用户</h2>
          <el-button @click="$router.push('/users')">返回用户列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名（3-20 个字符）"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码（至少 6 位）"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="formData.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="formData.role">
            <el-radio label="annotator">标注员</el-radio>
            <el-radio label="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="启用状态" prop="is_active">
          <el-switch v-model="formData.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            创建用户
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createUser } from '@/api/user'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'annotator',
  is_active: true
})

// 验证确认密码
const validateConfirmPassword = (rule: any, value: string, callback: Function) => {
  if (value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const rules = computed(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在 3-20 个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}))

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return

  loading.value = true
  try {
    await createUser({
      username: formData.username,
      password: formData.password,
      role: formData.role,
      is_active: formData.is_active
    })
    ElMessage.success('创建成功')
    router.push('/users')
  } catch (e: any) {
    // 解析后端返回的详细错误信息
    let errorMsg = '创建失败'
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
}

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields()
  formData.username = ''
  formData.password = ''
  formData.confirmPassword = ''
  formData.role = 'annotator'
  formData.is_active = true
}
</script>

<style scoped lang="scss">
.user-create {
  padding: 24px;

  .form-card {
    max-width: 600px;
    margin: 0 auto;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }
    }
  }
}
</style>
