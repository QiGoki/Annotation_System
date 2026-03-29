<script setup lang="ts">
/**
 * 数据导入页面 - StepFun风格
 * 支持批量上传多个 JSON/JSONL 文件
 */
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.id)

const uploading = ref(false)
const fileList = ref<File[]>([])
const dragOver = ref(false)
const importProgress = ref<{ current: number; total: number; message: string } | null>(null)
const importResults = ref<{ filename: string; count: number; error?: string }[]>([])

const totalFiles = computed(() => fileList.value.length)

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    // 添加新文件到列表（支持批量）
    const newFiles = Array.from(target.files)
    fileList.value = [...fileList.value, ...newFiles]
    // 重置 input 以便可以再次选择相同文件
    target.value = ''
  }
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  dragOver.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    const newFiles = Array.from(e.dataTransfer.files)
    fileList.value = [...fileList.value, ...newFiles]
  }
}

const removeFile = (index: number) => {
  fileList.value.splice(index, 1)
}

const clearFiles = () => {
  fileList.value = []
  importResults.value = []
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    alert('请选择文件')
    return
  }

  uploading.value = true
  importResults.value = []
  importProgress.value = { current: 0, total: fileList.value.length, message: '准备导入...' }

  try {
    for (let i = 0; i < fileList.value.length; i++) {
      const file = fileList.value[i]
      importProgress.value = {
        current: i + 1,
        total: fileList.value.length,
        message: `正在导入 ${file.name}...`
      }

      const formData = new FormData()
      formData.append('file', file)

      try {
        const res = await request.post(`/export/import?project_id=${projectId}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        importResults.value.push({
          filename: file.name,
          count: res.count || 0
        })
      } catch (e: any) {
        let errorMsg = '导入失败'
        if (e.response?.data?.detail) {
          const detail = e.response.data.detail
          if (typeof detail === 'string') {
            errorMsg = detail
          } else if (Array.isArray(detail)) {
            errorMsg = detail.map((err: any) => err.msg || '验证失败').join('; ')
          }
        }
        importResults.value.push({
          filename: file.name,
          count: 0,
          error: errorMsg
        })
      }
    }

    importProgress.value = { current: fileList.value.length, total: fileList.value.length, message: '导入完成' }

    const successCount = importResults.value.filter(r => !r.error).length
    const totalImported = importResults.value.reduce((sum, r) => sum + r.count, 0)

    if (successCount === fileList.value.length) {
      alert(`成功导入 ${totalImported} 条数据，共 ${successCount} 个文件`)
      router.push(`/projects/${projectId}`)
    } else {
      alert(`导入完成：成功 ${successCount} 个文件，失败 ${fileList.value.length - successCount} 个文件`)
    }
  } finally {
    uploading.value = false
    importProgress.value = null
  }
}
</script>

<template>
  <div class="page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">导入数据</h1>
        <span class="page-subtitle">上传 JSON/JSONL 格式数据文件，支持批量上传</span>
      </div>
      <button class="btn btn-secondary" @click="router.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"/>
          <polyline points="12 19 5 12 12 5"/>
        </svg>
        返回
      </button>
    </div>

    <!-- 上传卡片 -->
    <div class="card">
      <div
        class="upload-area"
        :class="{ 'upload-area-active': dragOver }"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop="handleDrop"
      >
        <input
          type="file"
          id="file-input"
          accept=".json,.jsonl"
          multiple
          @change="handleFileChange"
          style="display: none"
        />
        <label for="file-input" class="upload-content">
          <svg class="upload-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <div class="upload-text">
            拖拽文件或 <span class="upload-text-highlight">点击上传</span>
          </div>
          <div class="upload-tip">支持 JSON/JSONL 格式，可批量上传多个文件</div>
        </label>
      </div>

      <!-- 文件列表 -->
      <div v-if="fileList.length > 0" class="file-list">
        <div class="file-list-header">
          <span class="file-count">已选择 {{ totalFiles }} 个文件</span>
          <button class="btn btn-text btn-sm" @click="clearFiles">清空</button>
        </div>
        <div class="file-list-items">
          <div v-for="(file, index) in fileList" :key="index" class="file-item">
            <div class="file-item-info">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
            <button class="btn btn-text btn-sm" @click="removeFile(index)" :disabled="uploading">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 导入进度 -->
      <div v-if="importProgress" class="progress-section">
        <div class="progress-header">
          <span class="progress-text">{{ importProgress.message }}</span>
          <span class="progress-count">{{ importProgress.current }} / {{ importProgress.total }}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${(importProgress.current / importProgress.total) * 100}%` }"></div>
        </div>
      </div>

      <!-- 导入结果 -->
      <div v-if="importResults.length > 0" class="results-section">
        <div class="results-header">导入结果</div>
        <div class="results-list">
          <div v-for="result in importResults" :key="result.filename" class="result-item" :class="{ 'result-error': result.error }">
            <span class="result-filename">{{ result.filename }}</span>
            <span v-if="!result.error" class="result-success">成功导入 {{ result.count }} 条</span>
            <span v-else class="result-fail">{{ result.error }}</span>
          </div>
        </div>
      </div>

      <div class="card-footer">
        <button class="btn btn-secondary" @click="router.back()" :disabled="uploading">取消</button>
        <button class="btn btn-primary" :disabled="uploading || fileList.length === 0" @click="handleUpload">
          {{ uploading ? '导入中...' : `开始导入 (${totalFiles} 个文件)` }}
        </button>
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

.header-info {
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

.upload-area {
  border: 2px dashed #E5E7EB;
  border-radius: 12px;
  background: #F9FAFB;
  transition: all 0.2s ease;
  cursor: pointer;
}

.upload-area:hover,
.upload-area-active {
  border-color: #165DFF;
  background: #F0F5FF;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  cursor: pointer;
}

.upload-icon {
  color: #165DFF;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 14px;
  color: #111827;
  margin-bottom: 8px;
}

.upload-text-highlight {
  color: #165DFF;
}

.upload-tip {
  font-size: 12px;
  color: #6B7280;
}

/* 文件列表 */
.file-list {
  margin-top: 16px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  overflow: hidden;
}

.file-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.file-count {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.file-list-items {
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #F3F4F6;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-item-info svg {
  color: #6B7280;
}

.file-name {
  font-size: 14px;
  color: #111827;
}

.file-size {
  font-size: 12px;
  color: #9CA3AF;
}

/* 进度条 */
.progress-section {
  margin-top: 16px;
  padding: 16px;
  background: #F0F5FF;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-text {
  font-size: 14px;
  color: #165DFF;
  font-weight: 500;
}

.progress-count {
  font-size: 12px;
  color: #6B7280;
}

.progress-bar {
  height: 4px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #165DFF;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 导入结果 */
.results-section {
  margin-top: 16px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  overflow: hidden;
}

.results-header {
  padding: 12px 16px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.results-list {
  max-height: 150px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #F3F4F6;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item.result-error {
  background: #FEF2F2;
}

.result-filename {
  font-size: 14px;
  color: #111827;
}

.result-success {
  font-size: 12px;
  color: #10B981;
}

.result-fail {
  font-size: 12px;
  color: #EF4444;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #E5E7EB;
}

/* 按钮 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: #165DFF;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0E42D2;
}

.btn-primary:disabled {
  background: #E5E7EB;
  color: #9CA3AF;
  cursor: not-allowed;
}

.btn-secondary {
  background: #F3F4F6;
  color: #374151;
  border: 1px solid #E5E7EB;
}

.btn-secondary:hover:not(:disabled) {
  background: #E5E7EB;
}

.btn-secondary:disabled {
  background: #F3F4F6;
  color: #9CA3AF;
  cursor: not-allowed;
}

.btn-text {
  background: transparent;
  color: #165DFF;
  padding: 4px 8px;
}

.btn-text:hover:not(:disabled) {
  background: #F0F5FF;
}

.btn-text:disabled {
  color: #9CA3AF;
  cursor: not-allowed;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}
</style>