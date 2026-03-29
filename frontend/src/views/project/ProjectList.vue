<script setup lang="ts">
/**
 * 项目列表页面 - StepFun风格
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProjectList, deleteProject } from '@/api/project'
import type { Project } from '@/types/project'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(false)
const deleteConfirm = ref<{ show: boolean; project: Project | null }>({
  show: false,
  project: null
})

const loadProjects = async () => {
  loading.value = true
  try {
    projects.value = await getProjectList()
  } catch (e) {
    alert('加载项目列表失败')
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

const handleDelete = (project: Project) => {
  deleteConfirm.value = { show: true, project }
}

const confirmDelete = async () => {
  if (!deleteConfirm.value.project) return
  try {
    await deleteProject(deleteConfirm.value.project.id)
    alert('删除成功')
    loadProjects()
  } catch (e) {
    alert('删除失败')
  } finally {
    deleteConfirm.value = { show: false, project: null }
  }
}

const cancelDelete = () => {
  deleteConfirm.value = { show: false, project: null }
}

const getProgressColor = (percentage: number) => {
  if (percentage === 100) return 'var(--success-color)'
  if (percentage >= 50) return 'var(--warning-color)'
  return 'var(--text-tertiary)'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadProjects()
})
</script>

<template>
  <div class="page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">项目管理</h1>
      <button class="btn btn-primary" @click="handleCreate">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        创建项目
      </button>
    </div>

    <!-- 表格卡片 -->
    <div class="card table-card" :class="{ loading: loading }">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>项目名称</th>
            <th>描述</th>
            <th>进度</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in projects" :key="project.id">
            <td>{{ project.id }}</td>
            <td>
              <span class="link" @click="handleDetail(project.id)">{{ project.name }}</span>
            </td>
            <td>
              <span class="text-ellipsis">{{ project.description || '-' }}</span>
            </td>
            <td>
              <div class="progress">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{
                      width: project.task_count ? Math.round((project.completed_count / project.task_count) * 100) + '%' : '0%',
                      backgroundColor: getProgressColor(project.task_count ? Math.round((project.completed_count / project.task_count) * 100) : 0)
                    }"
                  />
                </div>
                <span class="progress-text">{{ project.completed_count }}/{{ project.task_count }}</span>
              </div>
            </td>
            <td>
              <span
                class="tag"
                :class="{
                  'tag-success': project.task_count && project.task_count - project.completed_count === 0,
                  'tag-warning': project.task_count && project.task_count - project.completed_count > 0,
                  'tag-default': !project.task_count
                }"
              >
                {{ project.task_count ? project.task_count - project.completed_count : 0 }} 待完成
              </span>
            </td>
            <td>{{ formatDate(project.created_at) }}</td>
            <td>
              <div class="actions">
                <button class="btn btn-text btn-sm" @click="handleDetail(project.id)">详情</button>
                <button class="btn btn-text btn-sm" @click="handleImport(project.id)">导入</button>
                <button class="btn btn-text btn-sm" @click="handleExport(project.id)">导出</button>
                <button class="btn btn-danger btn-sm" @click="handleDelete(project)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="projects.length === 0 && !loading">
            <td colspan="7" class="empty">暂无项目</td>
          </tr>
        </tbody>
      </table>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="deleteConfirm.show" class="dialog-overlay" @click.self="cancelDelete">
      <div class="dialog">
        <div class="dialog-title">确认删除</div>
        <div class="dialog-content">
          确定要删除项目 "{{ deleteConfirm.project?.name }}" 吗？此操作不可撤销。
        </div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="cancelDelete">取消</button>
          <button class="btn btn-primary" @click="confirmDelete">确定删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.table-card {
  position: relative;
  padding: 0;
  overflow: hidden;
}

.table-card.loading {
  min-height: 200px;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  background: #F9FAFB;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #6B7280;
  text-align: left;
  border-bottom: 1px solid #E5E7EB;
}

.table td {
  padding: 16px;
  font-size: 14px;
  color: #111827;
  border-bottom: 1px solid #E5E7EB;
}

.table tr:last-child td {
  border-bottom: none;
}

.table tr:hover td {
  background-color: #F9FAFB;
}

.link {
  color: #165DFF;
  cursor: pointer;
  font-weight: 500;
}

.link:hover {
  color: #0E42D2;
}

.text-ellipsis {
  max-width: 200px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #F3F4F6;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #6B7280;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 4px;
}

.empty {
  text-align: center;
  color: #9CA3AF;
  padding: 40px 16px;
}
</style>