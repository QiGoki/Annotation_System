<script setup lang="ts">
/**
 * 创建项目页面 - 基础配置
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

// 表单数据
const form = ref({
  name: '',
  description: '',
})

const loading = ref(false)

// 提交创建
const handleSubmit = async () => {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }

  loading.value = true
  try {
    // TODO: 调用 API 创建项目
    ElMessage.success('项目创建成功')
    router.push('/projects')
  } catch (error: any) {
    ElMessage.error('创建失败：' + error.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="project-create">
    <!-- 顶部 Header -->
    <div class="create-header">
      <h2>创建项目</h2>
      <div class="header-actions">
        <el-button @click="$router.back()">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">创建项目</el-button>
      </div>
    </div>

    <!-- 主体内容 - 基础配置 -->
    <div class="create-body">
      <el-card class="config-card">
        <template #header>
          <span>基础配置</span>
        </template>

        <el-form :model="form" label-width="100px" size="default">
          <el-form-item label="项目名称" required>
            <el-input v-model="form.name" placeholder="请输入项目名称" clearable />
          </el-form-item>
          <el-form-item label="项目描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              placeholder="请输入项目描述（可选）"
            />
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<style scoped lang="scss">
.project-create {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;

  .create-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: #fff;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    flex-shrink: 0;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .create-body {
    flex: 1;
    padding: 24px;
    overflow: auto;

    .config-card {
      max-width: 800px;
      margin: 0 auto;

      :deep(.el-card__header) {
        font-weight: 600;
      }
    }
  }
}
</style>
