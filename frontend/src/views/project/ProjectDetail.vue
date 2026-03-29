<script setup lang="ts">
/**
 * 项目详情页面 - StepFun风格
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProjectDetail, getProjectStatistics } from '@/api/project'
import { getTaskList, claimTask, releaseTask } from '@/api/task'
import { getProjectMembers, addProjectMember, removeProjectMember, updateMemberRole } from '@/api/project_members'
import type { Project, ProjectStatistics } from '@/types/project'
import type { Task } from '@/types/task'
import type { ProjectMember } from '@/api/project_members'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))

const project = ref<Project | null>(null)
const statistics = ref<ProjectStatistics | null>(null)
const tasks = ref<Task[]>([])
const members = ref<ProjectMember[]>([])
const loading = ref(false)

// 成员管理
const memberDialogVisible = ref(false)
const newMemberUserId = ref<number>(0)
const newMemberRole = ref('member')
const userList = ref<any[]>([])

const loadProject = async () => {
  loading.value = true
  try {
    project.value = await getProjectDetail(projectId.value)
    statistics.value = await getProjectStatistics(projectId.value)
    await loadTasks()
    await loadMembers()
  } catch (e) {
    alert('加载项目详情失败')
  } finally {
    loading.value = false
  }
}

const loadTasks = async () => {
  tasks.value = await getTaskList({ project_id: projectId.value })
}

const loadMembers = async () => {
  try {
    members.value = await getProjectMembers(projectId.value)
  } catch (e) {
    // 忽略错误
  }
}

const loadUserList = async () => {
  try {
    const { getUserList } = await import('@/api/user')
    userList.value = await getUserList()
  } catch (e) {
    alert('加载用户列表失败')
  }
}

const openAddMemberDialog = () => {
  memberDialogVisible.value = true
  newMemberUserId.value = 0
  newMemberRole.value = 'member'
  loadUserList()
}

const handleAddMember = async () => {
  if (!newMemberUserId.value) {
    alert('请选择用户')
    return
  }

  try {
    await addProjectMember(projectId.value, newMemberUserId.value, newMemberRole.value)
    alert('添加成员成功')
    memberDialogVisible.value = false
    loadMembers()
  } catch (e: any) {
    alert(e.response?.data?.detail || '添加失败')
  }
}

const removeConfirm = ref<{ show: boolean; member: ProjectMember | null }>({ show: false, member: null })

const handleRemoveMember = (member: ProjectMember) => {
  removeConfirm.value = { show: true, member }
}

const confirmRemoveMember = async () => {
  if (!removeConfirm.value.member) return
  try {
    await removeProjectMember(projectId.value, removeConfirm.value.member.user_id)
    alert('移除成功')
    loadMembers()
  } catch (e) {
    alert('移除失败')
  } finally {
    removeConfirm.value = { show: false, member: null }
  }
}

const handleUpdateRole = async (member: ProjectMember, role: string) => {
  try {
    await updateMemberRole(projectId.value, member.user_id, role)
    alert('更新成功')
    loadMembers()
  } catch (e) {
    alert('更新失败')
  }
}

const claimConfirm = ref<{ show: boolean; taskId: number | null }>({ show: false, taskId: null })

const handleClaim = (taskId: number) => {
  claimConfirm.value = { show: true, taskId }
}

const confirmClaim = async () => {
  if (!claimConfirm.value.taskId) return
  try {
    await claimTask(claimConfirm.value.taskId)
    alert('领取成功')
    loadTasks()
  } catch (e: any) {
    alert(e.response?.data?.detail || '领取失败')
  } finally {
    claimConfirm.value = { show: false, taskId: null }
  }
}

const releaseConfirm = ref<{ show: boolean; taskId: number | null }>({ show: false, taskId: null })

const handleRelease = (taskId: number) => {
  releaseConfirm.value = { show: true, taskId }
}

const confirmRelease = async () => {
  if (!releaseConfirm.value.taskId) return
  try {
    await releaseTask(releaseConfirm.value.taskId)
    alert('已释放')
    loadTasks()
  } catch (e) {
    alert('释放失败')
  } finally {
    releaseConfirm.value = { show: false, taskId: null }
  }
}

const getStatusClass = (status: string) => {
  const map: Record<string, string> = {
    pending: 'tag tag-primary',
    doing: 'tag tag-warning',
    completed: 'tag tag-success'
  }
  return map[status] || 'tag tag-default'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { pending: '待领取', doing: '标注中', completed: '已完成' }
  return map[status] || status
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getUserName = (userId: number | null) => {
  if (!userId) return '-'
  const member = members.value.find(m => m.user_id === userId)
  return member ? member.username : `用户${userId}`
}

onMounted(() => {
  loadProject()
})
</script>

<template>
  <div class="page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-info">
        <h1 class="page-title">{{ project?.name || '项目详情' }}</h1>
        <span class="page-subtitle">项目管理</span>
      </div>
      <div class="page-header-actions">
        <button class="btn btn-primary" @click="router.push(`/projects/${projectId}/configure`)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          设计标注页
        </button>
        <button class="btn btn-secondary" @click="router.push('/projects')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          返回
        </button>
      </div>
    </div>

    <!-- 基本信息 -->
    <div class="card">
      <h3 class="card-title">基本信息</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">项目名称</span>
          <span class="info-value">{{ project?.name }}</span>
        </div>
        <div class="info-item full-width">
          <span class="info-label">项目描述</span>
          <span class="info-value">{{ project?.description || '暂无描述' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ formatDate(project?.created_at) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">更新时间</span>
          <span class="info-value">{{ formatDate(project?.updated_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <h3 class="section-title">统计信息</h3>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ statistics?.total_tasks || 0 }}</div>
        <div class="stat-label">总任务数</div>
      </div>
      <div class="stat-card stat-pending">
        <div class="stat-value">{{ statistics?.pending_tasks || 0 }}</div>
        <div class="stat-label">待领取</div>
      </div>
      <div class="stat-card stat-doing">
        <div class="stat-value">{{ statistics?.doing_tasks || 0 }}</div>
        <div class="stat-label">标注中</div>
      </div>
      <div class="stat-card stat-completed">
        <div class="stat-value">{{ statistics?.completed_tasks || 0 }}</div>
        <div class="stat-label">已完成</div>
      </div>
    </div>

    <!-- 成员管理 -->
    <div class="section-header">
      <h3 class="section-title">项目成员</h3>
      <button class="btn btn-primary btn-sm" @click="openAddMemberDialog">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        添加成员
      </button>
    </div>
    <div class="card">
      <div class="member-count">共 {{ members.length }} 名成员</div>
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>用户名</th>
              <th>角色</th>
              <th>加入时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in members" :key="member.user_id">
              <td>{{ member.username }}</td>
              <td>
                <select class="role-select" :value="member.role" @change="handleUpdateRole(member, ($event.target as HTMLSelectElement).value)">
                  <option value="admin">管理员</option>
                  <option value="member">成员</option>
                </select>
              </td>
              <td>{{ formatDate(member.joined_at) }}</td>
              <td>
                <button class="btn btn-danger btn-sm" @click="handleRemoveMember(member)">移除</button>
              </td>
            </tr>
            <tr v-if="members.length === 0">
              <td colspan="4" class="empty">暂无成员</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 任务列表 -->
    <h3 class="section-title">任务列表</h3>
    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>数据源</th>
            <th>状态</th>
            <th>领取人</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>{{ task.id }}</td>
            <td>
              <div class="data-source">
                <span v-if="task.data_source?.type === 'image'">{{ task.data_source.filename || '图像' }}</span>
                <span v-else-if="task.data_source?.type === 'text'">{{ (task.data_source.content || '').substring(0, 30) }}...</span>
                <span v-else>-</span>
              </div>
            </td>
            <td>
              <span :class="getStatusClass(task.status)">{{ getStatusText(task.status) }}</span>
            </td>
            <td>{{ getUserName(task.assigned_to) }}</td>
            <td>{{ formatDate(task.created_at) }}</td>
            <td>
              <div class="actions">
                <button v-if="task.status === 'pending'" class="btn btn-primary btn-sm" @click="handleClaim(task.id)">领取</button>
                <template v-else-if="task.status === 'doing'">
                  <button class="btn btn-warning btn-sm" @click="handleRelease(task.id)">释放</button>
                  <button class="btn btn-primary btn-sm" @click="router.push(`/annotate/${task.id}`)">标注</button>
                </template>
                <span v-else class="tag tag-success">已完成</span>
              </div>
            </td>
          </tr>
          <tr v-if="tasks.length === 0">
            <td colspan="6" class="empty">暂无任务</td>
          </tr>
        </tbody>
      </table>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>
    </div>

    <!-- 添加成员对话框 -->
    <div v-if="memberDialogVisible" class="dialog-overlay" @click.self="memberDialogVisible = false">
      <div class="dialog">
        <div class="dialog-title">添加成员</div>
        <div class="dialog-body">
          <div class="form-group">
            <label class="form-label">选择用户</label>
            <select v-model="newMemberUserId" class="form-input">
              <option :value="0">请选择用户</option>
              <option v-for="user in userList" :key="user.id" :value="user.id">{{ user.username }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">角色</label>
            <div class="radio-group">
              <label class="radio">
                <input type="radio" v-model="newMemberRole" value="member" />
                <span class="radio-label">成员</span>
              </label>
              <label class="radio">
                <input type="radio" v-model="newMemberRole" value="admin" />
                <span class="radio-label">管理员</span>
              </label>
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="memberDialogVisible = false">取消</button>
          <button class="btn btn-primary" @click="handleAddMember">确定</button>
        </div>
      </div>
    </div>

    <!-- 确认对话框 -->
    <div v-if="removeConfirm.show" class="dialog-overlay" @click.self="removeConfirm.show = false">
      <div class="dialog">
        <div class="dialog-title">确认移除</div>
        <div class="dialog-content">确定要移除成员 "{{ removeConfirm.member?.username }}" 吗？</div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="removeConfirm.show = false">取消</button>
          <button class="btn btn-danger" @click="confirmRemoveMember">确定</button>
        </div>
      </div>
    </div>

    <div v-if="claimConfirm.show" class="dialog-overlay" @click.self="claimConfirm.show = false">
      <div class="dialog">
        <div class="dialog-title">确认领取</div>
        <div class="dialog-content">确定要领取此任务吗？</div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="claimConfirm.show = false">取消</button>
          <button class="btn btn-primary" @click="confirmClaim">确定</button>
        </div>
      </div>
    </div>

    <div v-if="releaseConfirm.show" class="dialog-overlay" @click.self="releaseConfirm.show = false">
      <div class="dialog">
        <div class="dialog-title">确认释放</div>
        <div class="dialog-content">确定要释放此任务吗？</div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="releaseConfirm.show = false">取消</button>
          <button class="btn btn-primary" @click="confirmRelease">确定</button>
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

.page-header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: #9CA3AF;
}

.page-header-actions {
  display: flex;
  gap: 8px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full-width {
  grid-column: span 2;
}

.info-label {
  font-size: 12px;
  font-weight: 500;
  color: #9CA3AF;
}

.info-value {
  font-size: 14px;
  color: #111827;
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

.member-count {
  font-size: 14px;
  color: #6B7280;
  margin-bottom: 12px;
}

.role-select {
  padding: 6px 12px;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  font-size: 14px;
  color: #111827;
  background: white;
  cursor: pointer;
}

.role-select:focus {
  outline: none;
  border-color: #165DFF;
}

.btn-warning {
  background-color: #F59E0B;
  color: white;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn-warning:hover {
  background-color: #D97706;
}

.data-source {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-card {
  position: relative;
  padding: 0;
  overflow: hidden;
}

.actions {
  display: flex;
  gap: 8px;
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

.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.empty {
  text-align: center;
  color: #9CA3AF;
  padding: 40px 16px;
}
</style>