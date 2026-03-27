<script setup lang="ts">
/**
 * 数据导入页面
 */
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.id)

const uploading = ref(false)
const fileList = ref<any[]>([])

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.error('请选择文件')
    return
  }

  uploading.value = true
  try {
    const file = fileList.value[0].raw
    const formData = new FormData()
    formData.append('file', file)

    const res = await request.post(`/export/import?project_id=${projectId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    ElMessage.success(res.message || '导入成功')
    router.push(`/projects/${projectId}`)
  } catch (e: any) {
    // 解析后端返回的详细错误信息
    let errorMsg = '导入失败'
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
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="task-import">
    <el-card>
      <template #header>
        <h2>导入数据</h2>
      </template>

      <el-upload
        drag
        :auto-upload="false"
        :on-change="(file: any) => { fileList = [file] }"
        accept=".json,.jsonl"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件或点击上传
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 JSON/JSONL 格式，每行一条数据
          </div>
        </template>
      </el-upload>

      <div class="actions" style="margin-top: 20px">
        <el-button @click="$router.back()">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          导入
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.task-import {
  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
