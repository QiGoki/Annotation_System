<script setup lang="ts">
/**
 * 创建项目页面 - StepFun风格
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createProject } from '@/api/project'

const router = useRouter()

const form = ref({
  name: '',
  description: '',
})

const loading = ref(false)
const errors = ref<{ name?: string }>({})

const validate = () => {
  errors.value = {}
  if (!form.value.name.trim()) {
    errors.value.name = '请输入项目名称'
    return false
  }
  return true
}

const handleSubmit = async () => {
  if (!validate()) return

  loading.value = true
  try {
    await createProject({
      name: form.value.name,
      description: form.value.description,
      config_json: { pages: [] },
    })
    alert('项目创建成功')
    router.push('/projects')
  } catch (error: any) {
    alert('创建失败：' + error.message)
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
        <h1 class="header-title">创建项目</h1>
        <span class="header-subtitle">新建标注项目</span>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="router.back()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          取消
        </button>
        <button class="btn btn-primary" :disabled="loading" @click="handleSubmit">
          <svg v-if="!loading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          创建项目
        </button>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="page-body">
      <div class="form-card">
        <h3 class="form-title">基础配置</h3>
        <form @submit.prevent="handleSubmit" class="form">
          <div class="form-group">
            <label class="form-label required">项目名称</label>
            <input
              v-model="form.name"
              type="text"
              class="form-input"
              :class="{ 'form-input-error': errors.name }"
              placeholder="请输入项目名称"
            />
            <span v-if="errors.name" class="form-error">{{ errors.name }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">项目描述</label>
            <textarea
              v-model="form.description"
              class="form-input form-textarea"
              rows="4"
              placeholder="请输入项目描述（可选）"
            ></textarea>
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
  max-width: 640px;
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

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.form-error {
  font-size: 12px;
  color: #EF4444;
  margin-top: 4px;
}

.form-input-error {
  border-color: #EF4444;
}
</style>