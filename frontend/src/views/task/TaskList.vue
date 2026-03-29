<script setup lang="ts">
/**
 * 任务列表页面 - StepFun风格
 */
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getMyProjects } from '@/api/project_members'
import { getTaskList, claimTask, releaseTask } from '@/api/task'
import { getProjectMembers } from '@/api/project_members'

const router = useRouter()

const tasks = ref<any[]>([])
const projects = ref<any[]>([])
const members = ref<any[]>([])
const loading = ref(false)
const claimLoading = ref<number | null>(null)

const filters = ref({
  project_id: undefined as number | undefined,
  status: undefined as string | undefined,
  assigned_to: undefined as number | undefined
})

const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

const loadProjects = async () => {
  try {
    projects.value = await getMyProjects()
  } catch (e) {
    alert('加载项目列表失败')
  }
}

const loadAllMembers = async () => {
  try {
    const allMembers = new Map<number, { user_id: number; username: string }>()
    for (const proj of projects.value) {
      try {
        const projMembers = await getProjectMembers(proj.id)
        projMembers.forEach(m => {
          allMembers.set(m.user_id, { user_id: m.user_id, username: m.username })
        })
      } catch (e) {}
    }
    members.value = Array.from(allMembers.values())
  } catch (e) {
    members.value = []
  }
}

const loadMembersForFilter = async (projectId: number) => {
  try {
    members.value = await getProjectMembers(projectId)
  } catch (e) {}
}

const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      project_id: filters.value.project_id,
      status: filters.value.status,
      assigned_to: filters.value.assigned_to,
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }
    Object.keys(params).forEach(key => {
      if (params[key] === undefined) delete params[key]
    })
    const result = await getTaskList(params)
    if (Array.isArray(result)) {
      tasks.value = result
      pagination.value.total = result.length
    } else {
      tasks.value = result.data || []
      pagination.value.total = result.total || 0
    }
  } catch (e) {
    alert('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

watch(() => filters.value.project_id, (newProjectId) => {
  if (newProjectId) {
    loadMembersForFilter(newProjectId)
  }
  filters.value.assigned_to = undefined
  pagination.value.page = 1
  loadTasks()
})

watch(() => [filters.value.status, filters.value.assigned_to, pagination.value.page], () => {
  loadTasks()
})

const confirmDialog = ref<{ show: boolean; type: string; taskId: number | null }>({
  show: false,
  type: '',
  taskId: null
})

const handleClaim = (taskId: number) => {
  confirmDialog.value = { show: true, type: 'claim', taskId }
}

const handleRelease = (taskId: number) => {
  confirmDialog.value = { show: true, type: 'release', taskId }
}

const confirmAction = async () => {
  if (!confirmDialog.value.taskId) return
  claimLoading.value = confirmDialog.value.taskId
  try {
    if (confirmDialog.value.type === 'claim') {
      await claimTask(confirmDialog.value.taskId)
      alert('领取成功')
    } else {
      await releaseTask(confirmDialog.value.taskId)
      alert('已释放任务')
    }
    loadTasks()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  } finally {
    claimLoading.value = null
    confirmDialog.value = { show: false, type: '', taskId: null }
  }
}

const memberNameMap = computed(() => {
  const map = new Map<number, string>()
  members.value.forEach(m => map.set(m.user_id, m.username))
  return map
})

const getStatusClass = (status: string) => {
  const map: Record<string, string> = {
    'pending': 'tag tag-primary',
    'doing': 'tag tag-warning',
    'completed': 'tag tag-success'
  }
  return map[status] || 'tag tag-default'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'pending': '待领取',
    'doing': '标注中',
    'completed': '已完成'
  }
  return map[status] || status
}

const getProjectName = (projectId: number) => {
  const proj = projects.value.find(p => p.id === projectId)
  return proj ? proj.name : '-'
}

const handleReset = () => {
  filters.value = {
    project_id: undefined,
    status: undefined,
    assigned_to: undefined
  }
  pagination.value.page = 1
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

const totalPages = computed(() => Math.ceil(pagination.value.total / pagination.value.page_size))

const changePage = (page: number) => {
  pagination.value.page = page
}

onMounted(() => {
  loadProjects().then(() => {
    loadAllMembers()
  })
  loadTasks()
})
</script>

<template>
  <div class="page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">任务列表</h1>
    </div>

    <!-- 筛选区域 -->
    <div class="card">
      <div class="filters">
        <div class="filter-group">
          <label class="filter-label">所属项目</label>
          <select v-model="filters.project_id" class="form-input filter-select">
            <option :value="undefined">全部项目</option>
            <option v-for="proj in projects" :key="proj.id" :value="proj.id">{{ proj.name }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">状态</label>
          <select v-model="filters.status" class="form-input filter-select-sm">
            <option :value="undefined">全部状态</option>
            <option value="pending">待领取</option>
            <option value="doing">标注中</option>
            <option value="completed">已完成</option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">领取人</label>
          <select v-model="filters.assigned_to" class="form-input filter-select">
            <option :value="undefined">全部成员</option>
            <option v-for="m in members" :key="m.user_id" :value="m.user_id">{{ m.username }}</option>
          </select>
        </div>

        <div class="filter-actions">
          <button class="btn btn-primary btn-sm" @click="loadTasks">查询</button>
          <button class="btn btn-secondary btn-sm" @click="handleReset">重置</button>
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>任务名称</th>
            <th>所属项目</th>
            <th>数据数量</th>
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
              <span class="task-name">{{ task.name || `任务 ${task.id}` }}</span>
            </td>
            <td>
              <span class="link">{{ getProjectName(task.project_id) }}</span>
            </td>
            <td>
              <span class="data-count">{{ Array.isArray(task.data_source) ? task.data_source.length : 1 }} 条</span>
            </td>
            <td>
              <span :class="getStatusClass(task.status)">{{ getStatusText(task.status) }}</span>
            </td>
            <td>{{ task.assigned_to ? (memberNameMap.get(task.assigned_to) || `用户${task.assigned_to}`) : '-' }}</td>
            <td>{{ formatDate(task.created_at) }}</td>
            <td>
              <button v-if="task.status === 'pending'" class="btn btn-primary btn-sm" @click="handleClaim(task.id)">领取</button>
              <div v-else-if="task.status === 'doing'" class="actions">
                <button class="btn btn-warning btn-sm" @click="handleRelease(task.id)">释放</button>
                <button class="btn btn-primary btn-sm" @click="router.push(`/annotate/${task.id}`)">标注</button>
              </div>
              <span v-else class="tag tag-success">已完成</span>
            </td>
          </tr>
          <tr v-if="tasks.length === 0 && !loading">
            <td colspan="8" class="empty">暂无任务</td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div v-if="pagination.total > 0" class="pagination">
        <span class="pagination-total">共 {{ pagination.total }} 条</span>
        <button class="pagination-btn" :disabled="pagination.page === 1" @click="changePage(pagination.page - 1)">上一页</button>
        <span class="pagination-info">{{ pagination.page }} / {{ totalPages }}</span>
        <button class="pagination-btn" :disabled="pagination.page >= totalPages" @click="changePage(pagination.page + 1)">下一页</button>
      </div>

      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>
    </div>

    <!-- 确认对话框 -->
    <div v-if="confirmDialog.show" class="dialog-overlay" @click.self="confirmDialog.show = false">
      <div class="dialog">
        <div class="dialog-title">{{ confirmDialog.type === 'claim' ? '确认领取' : '确认释放' }}</div>
        <div class="dialog-content">
          {{ confirmDialog.type === 'claim' ? '确定要领取此任务吗？' : '确定要释放此任务吗？释放后其他人可以领取。' }}
        </div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="confirmDialog.show = false">取消</button>
          <button class="btn btn-primary" @click="confirmAction">确定</button>
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

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.filter-select {
  width: 200px;
}

.filter-select-sm {
  width: 120px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.table-card {
  position: relative;
  padding: 0;
  overflow: hidden;
}

.link {
  color: #165DFF;
  font-weight: 500;
}

.task-name {
  font-weight: 500;
  color: #111827;
}

.data-count {
  color: #6B7280;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
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

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #E5E7EB;
}

.pagination-total {
  font-size: 14px;
  color: #6B7280;
}

.pagination-info {
  font-size: 14px;
  color: #111827;
}

.pagination-btn {
  padding: 8px 16px;
  font-size: 14px;
  color: #111827;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  border-color: #165DFF;
  color: #165DFF;
}

.pagination-btn:disabled {
  color: #D1D5DB;
  cursor: not-allowed;
}

.empty {
  text-align: center;
  color: #9CA3AF;
  padding: 40px 16px;
}
</style>