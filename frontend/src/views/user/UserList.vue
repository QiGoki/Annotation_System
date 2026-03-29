<script setup lang="ts">
/**
 * 用户列表页面 - StepFun风格
 */
import { ref, onMounted } from 'vue'
import { getUserList, createUser, updateUserStatus, deleteUser } from '@/api/user'
import type { User } from '@/types/user'

const users = ref<User[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({
  username: '',
  password: '',
  role: 'annotator',
})
const errors = ref<{ username?: string; password?: string }>({})

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await getUserList()
  } catch (e) {
    alert('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  dialogVisible.value = true
  form.value = {
    username: '',
    password: '',
    role: 'annotator',
  }
  errors.value = {}
}

const validate = () => {
  errors.value = {}
  let valid = true

  if (!form.value.username) {
    errors.value.username = '请输入用户名'
    valid = false
  } else if (form.value.username.length < 3 || form.value.username.length > 50) {
    errors.value.username = '用户名长度应在 3-50 个字符之间'
    valid = false
  }

  if (!form.value.password) {
    errors.value.password = '请输入密码'
    valid = false
  } else if (form.value.password.length < 6) {
    errors.value.password = '密码长度至少为 6 个字符'
    valid = false
  }

  return valid
}

const handleSubmit = async () => {
  if (!validate()) return

  try {
    await createUser(form.value)
    alert('创建成功')
    dialogVisible.value = false
    loadUsers()
  } catch (e: any) {
    let errorMsg = '创建失败'
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (typeof detail === 'string') {
        errorMsg = detail
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join('; ')
      }
    }
    alert(errorMsg)
  }
}

const confirmDialog = ref<{ show: boolean; type: string; user: User | null }>({
  show: false,
  type: '',
  user: null
})

const handleToggleStatus = (user: User) => {
  confirmDialog.value = { show: true, type: 'toggle', user }
}

const handleDelete = (user: User) => {
  confirmDialog.value = { show: true, type: 'delete', user }
}

const confirmAction = async () => {
  if (!confirmDialog.value.user) return

  try {
    if (confirmDialog.value.type === 'toggle') {
      await updateUserStatus(confirmDialog.value.user.id, !confirmDialog.value.user.is_active)
      alert(confirmDialog.value.user.is_active ? '已禁用用户' : '已启用用户')
    } else {
      await deleteUser(confirmDialog.value.user.id)
      alert('删除成功')
    }
    loadUsers()
  } catch (e) {
    alert('操作失败')
  } finally {
    confirmDialog.value = { show: false, type: '', user: null }
  }
}

const getRoleClass = (role: string) => {
  return role === 'admin' ? 'tag tag-error' : 'tag tag-primary'
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <button class="btn btn-primary" @click="handleCreate">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        创建用户
      </button>
    </div>

    <!-- 表格卡片 -->
    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td class="font-medium">{{ user.username }}</td>
            <td>
              <span :class="getRoleClass(user.role)">
                {{ user.role === 'admin' ? '管理员' : '标注员' }}
              </span>
            </td>
            <td>
              <span :class="user.is_active ? 'tag tag-success' : 'tag tag-error'">
                {{ user.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td>{{ new Date(user.created_at).toLocaleString('zh-CN') }}</td>
            <td>
              <div class="actions">
                <button class="btn btn-text btn-sm" @click="handleToggleStatus(user)">
                  {{ user.is_active ? '禁用' : '启用' }}
                </button>
                <button class="btn btn-danger btn-sm" @click="handleDelete(user)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="users.length === 0 && !loading">
            <td colspan="6" class="empty">暂无用户</td>
          </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>
    </div>

    <!-- 创建用户对话框 -->
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
      <div class="dialog">
        <div class="dialog-title">创建用户</div>
        <div class="dialog-body">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input
              v-model="form.username"
              type="text"
              class="form-input"
              :class="{ 'form-input-error': errors.username }"
              placeholder="请输入用户名"
            />
            <span v-if="errors.username" class="form-error">{{ errors.username }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">密码</label>
            <input
              v-model="form.password"
              type="password"
              class="form-input"
              :class="{ 'form-input-error': errors.password }"
              placeholder="请输入密码"
            />
            <span v-if="errors.password" class="form-error">{{ errors.password }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">角色</label>
            <div class="radio-group">
              <label class="radio">
                <input type="radio" v-model="form.role" value="annotator" />
                <span class="radio-label">标注员</span>
              </label>
              <label class="radio">
                <input type="radio" v-model="form.role" value="admin" />
                <span class="radio-label">管理员</span>
              </label>
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="dialogVisible = false">取消</button>
          <button class="btn btn-primary" @click="handleSubmit">创建</button>
        </div>
      </div>
    </div>

    <!-- 确认对话框 -->
    <div v-if="confirmDialog.show" class="dialog-overlay" @click.self="confirmDialog.show = false">
      <div class="dialog">
        <div class="dialog-title">
          {{ confirmDialog.type === 'toggle' ? '确认' : '确认删除' }}
        </div>
        <div class="dialog-content">
          {{ confirmDialog.type === 'toggle'
            ? `确定要${confirmDialog.user?.is_active ? '禁用' : '启用'}用户 "${confirmDialog.user?.username}" 吗？`
            : `确定要删除用户 "${confirmDialog.user?.username}" 吗？`
          }}
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

.table-card {
  position: relative;
  padding: 0;
  overflow: hidden;
}

.font-medium {
  font-weight: 500;
  color: #111827;
}

.actions {
  display: flex;
  gap: 4px;
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

.form-error {
  font-size: 12px;
  color: #EF4444;
  margin-top: 4px;
}

.form-input-error {
  border-color: #EF4444;
}

.empty {
  text-align: center;
  color: #9CA3AF;
  padding: 40px 16px;
}
</style>