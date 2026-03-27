<template>
  <div class="project-edit" v-loading="loading">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <h2>编辑项目</h2>
          <el-button @click="$router.push('/projects')">返回项目列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入项目名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="标注配置" prop="config_json">
          <ProjectConfigEditor v-model="formData.config_json" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            保存修改
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProjectDetail, updateProject } from '@/api/project'
import ProjectConfigEditor from '@/components/project/ProjectConfig.vue'
import type { ProjectConfig } from '@/types/project'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const loading = ref(false)
const submitting = ref(false)

const projectId = computed(() => Number(route.params.id))

const formData = reactive({
  name: '',
  description: '',
  config_json: {} as ProjectConfig
})

// 表单验证规则
const rules = computed(() => ({
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '项目名称长度应在 2-100 个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ],
  config_json: [
    { required: true, message: '请配置标注项目', trigger: 'change' }
  ]
}))

// 加载项目详情
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
  } catch (e: any) {
    ElMessage.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return

  submitting.value = true
  try {
    await updateProject(projectId.value, {
      name: formData.name,
      description: formData.description,
      config_json: formData.config_json
    })
    ElMessage.success('保存成功')
    router.push('/projects')
  } catch (e: any) {
    let errorMsg = '保存失败'
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (typeof detail === 'string') {
        errorMsg = detail
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map((err: any) => {
          const field = err.loc?.join('.') || '输入'
          const msg = err.msg || '验证失败'
          return `${field}: ${msg}`
        }).join('; ')
      }
    }
    ElMessage.error(errorMsg)
  } finally {
    submitting.value = false
  }
}

// 重置表单
const handleReset = () => {
  loadProject()
}

onMounted(() => {
  loadProject()
})
</script>

<style scoped lang="scss">
.project-edit {
  padding: 24px;

  .form-card {
    max-width: 800px;
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
