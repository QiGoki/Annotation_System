<script setup lang="ts">
/**
 * 标注页面独立布局
 * 不包含原生侧边栏和用户状态管理
 * 是一个完整的、全新的页面
 */
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 检查用户是否已登录，未登录则跳转到登录页
if (!userStore.token) {
  userStore.initUser().then(() => {
    if (!userStore.token) {
      router.push(`/login?redirect=${router.currentRoute.value.fullPath}`)
    }
  })
}
</script>

<template>
  <div class="annotation-layout">
    <!-- 内容区 -->
    <main class="annotation-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped lang="scss">
.annotation-layout {
  display: block;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: #f4f5f7;
}

.annotation-content {
  height: 100%;
  width: 100%;
  overflow: hidden;
}
</style>
