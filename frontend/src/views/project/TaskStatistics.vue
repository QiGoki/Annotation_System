<template>
  <div class="task-statistics" v-loading="loading">
    <el-container>
      <el-header>
        <h2>任务统计</h2>
        <el-button @click="$router.push('/projects')">返回项目列表</el-button>
      </el-header>

      <el-main>
        <!-- 项目选择 -->
        <el-card class="filter-card">
          <el-form :inline="true">
            <el-form-item label="选择项目">
              <el-select
                v-model="selectedProjectId"
                placeholder="请选择项目"
                @change="loadStatistics"
                style="width: 300px"
              >
                <el-option
                  v-for="project in projects"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 总览卡片 -->
        <el-row :gutter="20" class="overview-cards">
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-card">
                <div class="stat-icon" style="background: #409eff">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.totalTasks }}</div>
                  <div class="stat-label">总任务数</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-card">
                <div class="stat-icon" style="background: #909399">
                  <el-icon><Clock /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.pendingTasks }}</div>
                  <div class="stat-label">待标注</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-card">
                <div class="stat-icon" style="background: #e6a23c">
                  <el-icon><Edit /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.doingTasks }}</div>
                  <div class="stat-label">标注中</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-card">
                <div class="stat-icon" style="background: #67c23a">
                  <el-icon><Select /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.completedTasks }}</div>
                  <div class="stat-label">已完成</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 统计图表 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>任务状态分布</span>
              </template>
              <div class="chart-container">
                <div ref="pieChartRef" class="pie-chart"></div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                <span>标注人员工作量</span>
              </template>
              <div class="chart-container">
                <div ref="barChartRef" class="bar-chart"></div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 用户统计表格 -->
        <el-card>
          <template #header>
            <span>标注人员统计</span>
          </template>
          <el-table :data="userStats" stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色" />
            <el-table-column prop="assignedCount" label="分配任务数" sortable />
            <el-table-column prop="completedCount" label="完成数" sortable />
            <el-table-column prop="pendingCount" label="待完成" sortable />
            <el-table-column label="完成率">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.completionRate"
                  :color="getProgressColor(row.completionRate)"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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

// 加载项目列表
const loadProjects = async () => {
  try {
    const res = await getProjectList()
    projects.value = res
    if (res.length > 0) {
      selectedProjectId.value = res[0].id
      loadStatistics()
    }
  } catch (e: any) {
    ElMessage.error('加载项目列表失败')
  }
}

// 加载统计数据
const loadStatistics = async () => {
  if (!selectedProjectId.value) return

  loading.value = true
  try {
    // 获取所有任务
    const res = await getTaskList({ project_id: selectedProjectId.value, page: 1, page_size: 1000 })
    const tasks: Task[] = Array.isArray(res) ? res : (res as any).data || []

    // 计算统计
    stats.totalTasks = tasks.length
    stats.pendingTasks = tasks.filter(t => t.status === 'pending').length
    stats.doingTasks = tasks.filter(t => t.status === 'doing').length
    stats.completedTasks = tasks.filter(t => t.status === 'completed').length

    // 用户统计
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

    // 更新图表（如果有 ECharts）
    updateCharts()
  } catch (e: any) {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

// 更新图表
const updateCharts = () => {
  // 这里可以集成 ECharts
  // 简化版本：仅显示数据
  console.log('更新图表', stats)
}

// 获取进度条颜色
const getProgressColor = (percentage: number) => {
  if (percentage >= 80) return '#67c23a'
  if (percentage >= 50) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped lang="scss">
.task-statistics {
  min-height: 100vh;
  background: #f5f7fa;

  .el-header {
    background: #fff;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }

  .el-main {
    padding: 20px;
  }

  .filter-card {
    margin-bottom: 20px;
  }

  .overview-cards {
    margin-bottom: 20px;

    .stat-card {
      display: flex;
      align-items: center;
      gap: 16px;

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 28px;
      }

      .stat-info {
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: #303133;
        }

        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }

  .chart-container {
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #909399;
  }
}
</style>
