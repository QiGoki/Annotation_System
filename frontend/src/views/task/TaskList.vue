<script setup lang="ts">
/**
 * 任务列表页面 - 支持任务领取
 */
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyProjects } from '@/api/project_members'
import { getTaskList, claimTask, releaseTask } from '@/api/task'
import { getProjectMembers } from '@/api/project_members'

const router = useRouter()

// 数据
const tasks = ref<any[]>([])
const projects = ref<any[]>([])
const members = ref<any[]>([])
const loading = ref(false)
const claimLoading = ref<number | null>(null)

// 筛选条件
const filters = ref({
  project_id: undefined as number | undefined,
  status: undefined as string | undefined,
  assigned_to: undefined as number | undefined
})

// 分页
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

// 加载我的项目
const loadProjects = async () => {
  try {
    projects.value = await getMyProjects()
  } catch (e: any) {
    ElMessage.error('加载项目列表失败')
  }
}

// 加载所有项目的成员（用于显示领取人名称）
const loadAllMembers = async () => {
  try {
    const allMembers = new Map<number, { user_id: number; username: string }>()
    for (const proj of projects.value) {
      try {
        const projMembers = await getProjectMembers(proj.id)
        projMembers.forEach(m => {
          allMembers.set(m.user_id, { user_id: m.user_id, username: m.username })
        })
      } catch (e) {
        // 忽略单个项目的成员加载失败
      }
    }
    members.value = Array.from(allMembers.values())
  } catch (e: any) {
    members.value = []
  }
}

// 加载成员列表（用于筛选器）
const loadMembersForFilter = async (projectId: number) => {
  try {
    const projMembers = await getProjectMembers(projectId)
    // 更新成员列表用于筛选器显示
    members.value = projMembers
  } catch (e: any) {
    // 忽略错误
  }
}

// 加载任务列表
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

    // 清除未定义的参数
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
  } catch (e: any) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 项目变化时重新加载
watch(() => filters.value.project_id, (newProjectId) => {
  if (newProjectId) {
    loadMembersForFilter(newProjectId)
  }
  filters.value.assigned_to = undefined
  pagination.value.page = 1
  loadTasks()
})

// 其他筛选条件变化时重新加载
watch(() => [filters.value.status, filters.value.assigned_to, pagination.value.page], () => {
  loadTasks()
})

// 领取任务
const handleClaim = async (taskId: number) => {
  claimLoading.value = taskId
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
  } finally {
    claimLoading.value = null
  }
}

// 释放任务
const handleRelease = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要释放此任务吗？释放后其他人可以领取。', '确认释放', {
      type: 'warning'
    })
    await releaseTask(taskId)
    ElMessage.success('已释放任务')
    loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') {
      let errorMsg = '释放失败'
      if (e.response?.data?.detail) {
        errorMsg = e.response.data.detail
      }
      ElMessage.error(errorMsg)
    }
  }
}

// 获取用户名称 - 使用 Map 缓存
const getUserName = (userId: number | null) => {
  if (!userId) return '-'
  const member = members.value.find(m => m.user_id === userId)
  return member ? member.username : `用户${userId}`
}

// 创建成员 ID 到用户名的映射
const memberNameMap = computed(() => {
  const map = new Map<number, string>()
  members.value.forEach(m => map.set(m.user_id, m.username))
  return map
})

// 状态标签类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'pending': 'info',
    'doing': 'warning',
    'completed': 'success'
  }
  return map[status] || 'info'
}

// 状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'pending': '待领取',
    'doing': '标注中',
    'completed': '已完成'
  }
  return map[status] || status
}

// 获取项目名称
const getProjectName = (projectId: number) => {
  const proj = projects.value.find(p => p.id === projectId)
  return proj ? proj.name : '-'
}

// 重置筛选
const handleReset = () => {
  filters.value = {
    project_id: undefined,
    status: undefined,
    assigned_to: undefined
  }
  pagination.value.page = 1
}

onMounted(() => {
  loadProjects().then(() => {
    // 项目加载完成后加载所有成员
    loadAllMembers()
  })
  loadTasks()
})
</script>

<template>
  <div class="task-list">
    <div class="header">
      <h2>任务列表</h2>
    </div>

    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="所属项目">
          <el-select
            v-model="filters.project_id"
            placeholder="全部项目"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="proj in projects"
              :key="proj.id"
              :label="proj.name"
              :value="proj.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            placeholder="全部状态"
            clearable
            style="width: 120px"
          >
            <el-option label="待领取" value="pending" />
            <el-option label="标注中" value="doing" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>

        <el-form-item label="领取人">
          <el-select
            v-model="filters.assigned_to"
            placeholder="全部成员"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="m in members"
              :key="m.user_id"
              :label="m.username"
              :value="m.user_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadTasks">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务列表 -->
    <el-card v-loading="loading">
      <el-table :data="tasks" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="所属项目" width="150">
          <template #default="{ row }">
            {{ getProjectName(row.project_id) }}
          </template>
        </el-table-column>
        <el-table-column label="数据源" min-width="200">
          <template #default="{ row }">
            <span v-if="row.data_source?.type === 'image'">
              <el-icon><picture /></el-icon>
              {{ row.data_source.filename || '图像' }}
            </span>
            <span v-else-if="row.data_source?.type === 'text'">
              <el-icon><document /></el-icon>
              {{ (row.data_source.content || '').substring(0, 30) }}...
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="领取人" width="120">
          <template #default="{ row }">
            {{ row.assigned_to ? (memberNameMap.get(row.assigned_to) || `用户${row.assigned_to}`) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <!-- 待领取状态 -->
            <el-button
              v-if="row.status === 'pending'"
              type="primary"
              size="small"
              :loading="claimLoading === row.id"
              @click="handleClaim(row.id)"
            >
              领取
            </el-button>

            <!-- 已领取状态 -->
            <template v-else-if="row.status === 'doing'">
              <el-button
                type="warning"
                size="small"
                @click="handleRelease(row.id)"
              >
                释放
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="$router.push(`/annotate/${row.id}`)"
              >
                标注
              </el-button>
            </template>

            <!-- 已完成状态 -->
            <el-tag v-else type="success" size="small">
              已完成
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @change="loadTasks"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.task-list {
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>
