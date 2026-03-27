<script setup lang="ts">
/**
 * 用户列表页面
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, createUser, updateUserStatus, deleteUser } from '@/api/user'
import type { User } from '@/types/user'

const users = ref<User[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const form = ref({
  username: '',
  password: '',
  role: 'annotator',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应在 3-50 个字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur' },
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' },
  ],
}

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await getUserList()
  } catch (e: any) {
    ElMessage.error('加载用户列表失败')
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
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    try {
      await createUser(form.value)
      ElMessage.success('创建成功')
      dialogVisible.value = false
      loadUsers()
    } catch (e: any) {
      // 解析后端返回的详细错误信息
      let errorMsg = '创建失败'
      if (e.response?.data?.detail) {
        const detail = e.response.data.detail
        if (typeof detail === 'string') {
          errorMsg = detail
        } else if (Array.isArray(detail)) {
          // Pydantic 验证错误数组
          errorMsg = detail.map((err: any) => {
            const field = err.loc?.join('.') || '输入'
            const msg = err.msg || '验证失败'
            return `${field}: ${msg}`
          }).join('; ')
        }
      }
      ElMessage.error(errorMsg)
    }
  })
}

const handleToggleStatus = async (user: User) => {
  try {
    await updateUserStatus(user.id, !user.is_active)
    ElMessage.success(user.is_active ? '已禁用用户' : '已启用用户')
    loadUsers()
  } catch (e: any) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (user: User) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${user.username}" 吗？`, '确认删除', {
      type: 'warning',
    })
    await deleteUser(user.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="user-list">
    <div class="header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="handleCreate">创建用户</el-button>
    </div>

    <el-table :data="users" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'">
            {{ row.role === 'admin' ? '管理员' : '标注员' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleToggleStatus(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button
            link
            type="danger"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建用户对话框 -->
    <el-dialog v-model="dialogVisible" title="创建用户" width="400px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio value="annotator">标注员</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.user-list {
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
