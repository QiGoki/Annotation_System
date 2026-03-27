<script setup lang="ts">
/**
 * 项目列表页面
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProjectList, deleteProject } from '@/api/project'
import type { Project } from '@/types/project'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(false)

const loadProjects = async () => {
  loading.value = true
  try {
    projects.value = await getProjectList()
  } catch (e: any) {
    ElMessage.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  router.push('/projects/create')
}

const handleDetail = (id: number) => {
  router.push(`/projects/${id}`)
}

const handleImport = (id: number) => {
  router.push(`/projects/${id}/import`)
}

const handleExport = (id: number) => {
  window.open(`/api/v1/export?project_id=${id}&format=jsonl`)
}

const handleDelete = async (project: Project) => {
  try {
    await ElMessageBox.confirm(`确定要删除项目 "${project.name}" 吗？`, '确认删除', {
      type: 'warning',
    })
    await deleteProject(project.id)
    ElMessage.success('删除成功')
    loadProjects()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getProgressColor = (percentage: number) => {
  if (percentage === 100) return '#67c23a'  // green/success
  if (percentage >= 50) return '#e6a23c'    // orange/warning
  return '#909399'                           // gray/info
}

onMounted(() => {
  loadProjects()
})
</script>

<template>
  <div class="project-list">
    <div class="header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="handleCreate">创建项目</el-button>
    </div>

    <el-table :data="projects" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="项目名称" min-width="200" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="进度" width="200">
        <template #default="{ row }">
          <el-progress
            :percentage="row.task_count ? Math.round((row.completed_count / row.task_count) * 100) : 0"
            :color="getProgressColor(row.task_count ? Math.round((row.completed_count / row.task_count) * 100) : 0)"
          />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag>
            {{ row.task_count ? row.task_count - row.completed_count : 0 }} 待完成
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleDetail(row.id)">详情</el-button>
          <el-button link type="primary" @click="handleImport(row.id)">导入</el-button>
          <el-button link type="primary" @click="handleExport(row.id)">导出</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped lang="scss">
.project-list {
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }
}
</style>
