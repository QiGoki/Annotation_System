<script setup lang="ts">
/**
 * 编辑项目页面 - StepFun风格
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProjectDetail, updateProject } from '@/api/project'
import ProjectConfigEditor from '@/components/project/ProjectConfig.vue'
import type { ProjectConfig } from '@/types/project'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)

const projectId = computed(() => Number(route.params.id))

const formData = reactive({
  name: '',
  description: '',
  config_json: {} as ProjectConfig
})

const errors = ref<{ name?: string }>({})

const loadProject = async () => {
  loading.value = true
  try {
    const res = await getProjectDetail(projectId.value)
    formData.name = res.name
    formData.description = res.description || ''
    formData.config_json = res.config_json || {
      version: '1.0',
      components: []
    }
  } catch (e) {
    alert('加载项目失败')
  } finally {
    loading.value = false
  }
}

const validate = () => {
  errors.value = {}
  if (!formData.name.trim()) {
    errors.value.name = '请输入项目名称'
    return false
  }
  if (formData.name.length < 2 || formData.name.length > 100) {
    errors.value.name = '项目名称长度应在 2-100 个字符之间'
    return false
  }
  return true
}

const handleSubmit = async () => {
  if (!validate()) return

  submitting.value = true
  try {
    await updateProject(projectId.value, {
      name: formData.name,
      description: formData.description,
      config_json: formData.config_json
    })
    alert('保存成功')
    router.push('/projects')
  } catch (e: any) {
    let errorMsg = '保存失败'
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
    submitting.value = false
  }
}

onMounted(() => {
  loadProject()
})
</script>

<template>
  <div class="page" v-if="!loading">
    <!-- 顶部 Header -->
    <div class="page-header-bar">
      <div class="header-info">
        <h1 class="header-title">编辑项目</h1>
        <span class="header-subtitle">修改项目信息</span>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="router.push('/projects')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          返回
        </button>
        <button class="btn btn-primary" :disabled="submitting" @click="handleSubmit">
          <svg v-if="!submitting" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          保存修改
        </button>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="page-body">
      <div class="form-card">
        <h3 class="form-title">项目信息</h3>
        <form class="form">
          <div class="form-group">
            <label class="form-label required">项目名称</label>
            <input
              v-model="formData.name"
              type="text"
              class="form-input"
              :class="{ 'form-input-error': errors.name }"
              placeholder="请输入项目名称"
              maxlength="100"
            />
            <span v-if="errors.name" class="form-error">{{ errors.name }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">项目描述</label>
            <textarea
              v-model="formData.description"
              class="form-input form-textarea"
              rows="4"
              placeholder="请输入项目描述"
              maxlength="500"
            ></textarea>
          </div>

          <div class="form-group">
            <label class="form-label required">标注配置</label>
            <ProjectConfigEditor v-model="formData.config_json" />
          </div>
        </form>
      </div>
    </div>
  </div>

  <div v-else class="page-loading">
    <div class="loading-spinner"></div>
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

.page-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}
</style>