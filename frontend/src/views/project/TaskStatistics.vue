<script setup lang="ts">
/**
 * 任务统计页面 - StepFun风格
 */
import { ref, reactive, onMounted } from 'vue'
import { getProjectList } from '@/api/project'
import { getTaskList } from '@/api/task'
import type { Project } from '@/types/project'
import type { Task } from '@/types/task'

const loading = ref(false)
const projects = ref<Project[]>([])
const selectedProjectId = ref<number | null>(null)

const stats = reactive({
  totalTasks: 0,
  pendingTasks: 0,
  doingTasks: 0,
  completedTasks: 0
})

const userStats = ref<Array<{
  username: string
  role: string
  assignedCount: number
  completedCount: number
  pendingCount: number
  completionRate: number
}>>([])

const loadProjects = async () => {
  try {
    projects.value = await getProjectList()
    if (projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id
      loadStatistics()
    }
  } catch (e) {
    alert('加载项目列表失败')
  }
}

const loadStatistics = async () => {
  if (!selectedProjectId.value) return

  loading.value = true
  try {
    const res = await getTaskList({ project_id: selectedProjectId.value, page: 1, page_size: 1000 })
    const tasks: Task[] = Array.isArray(res) ? res : (res as any).data || []

    stats.totalTasks = tasks.length
    stats.pendingTasks = tasks.filter(t => t.status === 'pending').length
    stats.doingTasks = tasks.filter(t => t.status === 'doing').length
    stats.completedTasks = tasks.filter(t => t.status === 'completed').length

    const userTaskMap = new Map<string, {
      username: string
      role: string
      assigned: number
      completed: number
      pending: number
    }>()

    tasks.forEach(task => {
      const username = task.assigned_to ? `用户${task.assigned_to}` : '未分配'
      if (!userTaskMap.has(username)) {
        userTaskMap.set(username, {
          username,
          role: '标注员',
          assigned: 0,
          completed: 0,
          pending: 0
        })
      }
      const user = userTaskMap.get(username)!
      user.assigned++
      if (task.status === 'completed') {
        user.completed++
      } else if (task.status === 'pending') {
        user.pending++
      }
    })

    userStats.value = Array.from(userTaskMap.values()).map(u => ({
      username: u.username,
      role: u.role,
      assignedCount: u.assigned,
      completedCount: u.completed,
      pendingCount: u.pending,
      completionRate: u.assigned > 0 ? Math.round((u.completed / u.assigned) * 100) : 0
    }))
  } catch (e) {
    alert('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const getProgressColor = (percentage: number) => {
  if (percentage >= 80) return '#10B981'
  if (percentage >= 50) return '#F59E0B'
  return '#EF4444'
}

onMounted(() => {
  loadProjects()
})
</script>

<template>
  <div class="page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">任务统计</h1>
      <button class="btn btn-secondary" @click="$router.push('/projects')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"/>
          <polyline points="12 19 5 12 12 5"/>
        </svg>
        返回
      </button>
    </div>

    <!-- 项目选择 -->
    <div class="card">
      <div class="filter-row">
        <label class="filter-label">选择项目</label>
        <select v-model="selectedProjectId" class="form-input filter-select" @change="loadStatistics">
          <option v-for="project in projects" :key="project.id" :value="project.id">
            {{ project.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalTasks }}</div>
        <div class="stat-label">总任务数</div>
      </div>
      <div class="stat-card stat-pending">
        <div class="stat-value">{{ stats.pendingTasks }}</div>
        <div class="stat-label">待领取</div>
      </div>
      <div class="stat-card stat-doing">
        <div class="stat-value">{{ stats.doingTasks }}</div>
        <div class="stat-label">标注中</div>
      </div>
      <div class="stat-card stat-completed">
        <div class="stat-value">{{ stats.completedTasks }}</div>
        <div class="stat-label">已完成</div>
      </div>
    </div>

    <!-- 用户统计表格 -->
    <h3 class="section-title">标注人员统计</h3>
    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>角色</th>
            <th>分配任务数</th>
            <th>完成数</th>
            <th>待完成</th>
            <th>完成率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in userStats" :key="user.username">
            <td class="font-medium">{{ user.username }}</td>
            <td><span class="tag tag-primary">{{ user.role }}</span></td>
            <td>{{ user.assignedCount }}</td>
            <td>{{ user.completedCount }}</td>
            <td>{{ user.pendingCount }}</td>
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{
                      width: user.completionRate + '%',
                      backgroundColor: getProgressColor(user.completionRate)
                    }"
                  />
                </div>
                <span class="progress-text">{{ user.completionRate }}%</span>
              </div>
            </td>
          </tr>
          <tr v-if="userStats.length === 0">
            <td colspan="6" class="empty">暂无数据</td>
          </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
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

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

.filter-select {
  width: 300px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #9CA3AF;
}

.stat-pending {
  background: #DBEAFE;
}

.stat-pending .stat-value,
.stat-pending .stat-label {
  color: #3B82F6;
}

.stat-doing {
  background: #FEF3C7;
}

.stat-doing .stat-value,
.stat-doing .stat-label {
  color: #F59E0B;
}

.stat-completed {
  background: #D1FAE5;
}

.stat-completed .stat-value,
.stat-completed .stat-label {
  color: #10B981;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.table-card {
  position: relative;
  padding: 0;
  overflow: hidden;
}

.font-medium {
  font-weight: 500;
  color: #111827;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  width: 100px;
  height: 6px;
  background: #F3F4F6;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
}

.progress-text {
  font-size: 12px;
  color: #6B7280;
}

.empty {
  text-align: center;
  color: #9CA3AF;
  padding: 40px 16px;
}
</style>