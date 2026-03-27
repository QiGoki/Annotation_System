<script setup lang="ts">
/**
 * 项目详情页面 - 含成员管理
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProjectDetail, getProjectStatistics } from '@/api/project'
import { getTaskList, claimTask, releaseTask } from '@/api/task'
import { getProjectMembers, addProjectMember, removeProjectMember, updateMemberRole } from '@/api/project_members'
import type { Project, ProjectStatistics } from '@/types/project'
import type { Task } from '@/types/task'
import type { ProjectMember } from '@/api/project_members'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))

const project = ref<Project | null>(null)
const statistics = ref<ProjectStatistics | null>(null)
const tasks = ref<Task[]>([])
const members = ref<ProjectMember[]>([])
const loading = ref(false)

// 成员管理
const memberDialogVisible = ref(false)
const userSelectVisible = ref(false)
const newMemberUserId = ref<number>(0)
const newMemberRole = ref('member')
const currentUser = ref({ id: 1, role: 'admin' }) // TODO: 从 store 获取

// 用户列表（用于选择）
const userList = ref<any[]>([])

const loadProject = async () => {
  loading.value = true
  try {
    project.value = await getProjectDetail(projectId.value)
    statistics.value = await getProjectStatistics(projectId.value)
    await loadTasks()
    await loadMembers()
  } catch (e: any) {
    ElMessage.error('加载项目详情失败')
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
  } catch (e: any) {
    // 忽略错误
  }
}

const loadUserList = async () => {
  try {
    const { getUserList } = await import('@/api/user')
    userList.value = await getUserList()
  } catch (e: any) {
    ElMessage.error('加载用户列表失败')
  }
}

// 打开添加成员对话框
const openAddMemberDialog = () => {
  memberDialogVisible.value = true
  newMemberUserId.value = 0
  newMemberRole.value = 'member'
  loadUserList()
}

// 添加成员
const handleAddMember = async () => {
  if (!newMemberUserId.value) {
    ElMessage.error('请选择用户')
    return
  }

  try {
    await addProjectMember(projectId.value, newMemberUserId.value, newMemberRole.value)
    ElMessage.success('添加成员成功')
    memberDialogVisible.value = false
    loadMembers()
  } catch (e: any) {
    let errorMsg = '添加失败'
    if (e.response?.data?.detail) {
      errorMsg = e.response.data.detail
    }
    ElMessage.error(errorMsg)
  }
}

// 移除成员
const handleRemoveMember = async (member: ProjectMember) => {
  try {
    await ElMessageBox.confirm(`确定要移除成员 "${member.username}" 吗？`, '确认移除', {
      type: 'warning'
    })
    await removeProjectMember(projectId.value, member.user_id)
    ElMessage.success('移除成功')
    loadMembers()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

// 更新角色
const handleUpdateRole = async (member: ProjectMember, role: string) => {
  try {
    await updateMemberRole(projectId.value, member.user_id, role)
    ElMessage.success('更新成功')
    loadMembers()
  } catch (e: any) {
    ElMessage.error('更新失败')
  }
}

// 领取任务
const handleClaim = async (taskId: number) => {
  try {
    await claimTask(taskId)
    ElMessage.success('领取成功')
    loadTasks()
  } catch (e: any) {
    let errorMsg = '领取失败'
    if (e.response?.data?.detail) {
      errorMsg = e.response.data.detail
    }
    ElMessage.error(errorMsg)
  }
}

// 释放任务
const handleRelease = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要释放此任务吗？', '确认释放', { type: 'warning' })
    await releaseTask(taskId)
    ElMessage.success('已释放')
    loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('释放失败')
    }
  }
}

const getStatusTagType = (status: string) => {
  const map: Record<string, string> = { pending: 'info', doing: 'warning', completed: 'success' }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { pending: '待领取', doing: '标注中', completed: '已完成' }
  return map[status] || status
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
  <div class="project-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>{{ project?.name || '项目详情' }}</h2>
          <div class="header-actions">
            <el-button type="primary" @click="$router.push(`/projects/${projectId}/configure`)">设计标注页</el-button>
            <el-button @click="$router.push('/projects')">返回</el-button>
          </div>
        </div>
      </template>

      <!-- 基本信息 -->
      <el-card class="info-card" style="margin-top: 16px">
        <el-descriptions :column="2">
          <el-descriptions-item label="项目名称">{{ project?.name }}</el-descriptions-item>
          <el-descriptions-item label="项目描述" :span="2">{{ project?.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ project ? new Date(project.created_at).toLocaleString('zh-CN') : '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ project ? new Date(project.updated_at).toLocaleString('zh-CN') : '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 统计信息 -->
      <h3 class="section-title">统计信息</h3>
      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="总任务数" :value="statistics?.total_tasks || 0" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="待领取" :value="statistics?.pending_tasks || 0" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="标注中" :value="statistics?.doing_tasks || 0" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="已完成" :value="statistics?.completed_tasks || 0" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 成员管理 -->
      <h3 class="section-title">项目成员</h3>
      <el-card class="members-card" style="margin-top: 16px">
        <div class="members-header">
          <span>共 {{ members.length }} 名成员</span>
          <el-button type="primary" size="small" @click="openAddMemberDialog">添加成员</el-button>
        </div>
        <el-table :data="members" size="small" style="margin-top: 12px">
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="role" label="角色" width="120">
            <template #default="{ row }">
              <el-select v-model="row.role" size="small" @change="handleUpdateRole(row, $event)">
                <el-option label="管理员" value="admin" />
                <el-option label="成员" value="member" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="joined_at" label="加入时间" width="180">
            <template #default="{ row }">
              {{ row.joined_at ? new Date(row.joined_at).toLocaleString('zh-CN') : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="handleRemoveMember(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 任务列表 -->
      <h3 class="section-title">任务列表</h3>
      <el-card class="task-card" style="margin-top: 16px">
        <el-table :data="tasks" style="margin-top: 0" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="数据源" min-width="200">
          <template #default="{ row }">
            <span v-if="row.data_source?.type === 'image'">
              <el-icon><picture /></el-icon> {{ row.data_source.filename || '图像' }}
            </span>
            <span v-else-if="row.data_source?.type === 'text'">
              <el-icon><document /></el-icon> {{ (row.data_source.content || '').substring(0, 30) }}...
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="领取人" width="120">
          <template #default="{ row }">
            {{ getUserName(row.assigned_to) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              type="primary"
              size="small"
              @click="handleClaim(row.id)"
            >领取</el-button>
            <template v-else-if="row.status === 'doing'">
              <el-button type="warning" size="small" @click="handleRelease(row.id)">释放</el-button>
              <el-button
                type="primary"
                size="small"
                @click="$router.push(`/annotate/${row.id}`)"
              >标注</el-button>
            </template>
            <el-tag v-else type="success" size="small">已完成</el-tag>
          </template>
        </el-table-column>
      </el-table>
      </el-card>
    </el-card>

    <!-- 添加成员对话框 -->
    <el-dialog v-model="memberDialogVisible" title="添加成员" width="400px">
      <el-form label-width="80px">
        <el-form-item label="选择用户" required>
          <el-select v-model="newMemberUserId" placeholder="请选择用户" style="width: 100%">
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" required>
          <el-radio-group v-model="newMemberRole">
            <el-radio value="member">成员</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddMember">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.project-detail {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .section-title {
    margin: 24px 0 12px;
    font-size: 16px;
    font-weight: 600;
    color: #333;
  }

  .info-card, .members-card, .task-card {
    :deep(.el-card__body) {
      padding: 16px;
    }
  }

  .stat-card {
    :deep(.el-card__body) {
      padding: 12px 16px;
    }
  }

  .members-card {
    .members-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style>
