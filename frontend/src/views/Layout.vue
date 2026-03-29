<script setup lang="ts">
/**
 * 布局组件 - StepFun风格
 */
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const userName = computed(() => userStore.user?.username || '')
const userRole = computed(() => userStore.user?.role === 'admin' ? '管理员' : '标注员')

const handleLogout = async () => {
  await userStore.logout()
  alert('已退出登录')
  router.push('/login')
}

const navItems = computed(() => {
  const items: { path: string; label: string }[] = []

  if (userStore.user?.role === 'admin') {
    items.push({ path: '/projects', label: '项目管理' })
  }

  items.push({ path: '/tasks', label: '任务列表' })

  if (userStore.user?.role === 'admin') {
    items.push({ path: '/users', label: '用户管理' })
  }

  return items
})

const isActive = (path: string) => {
  return route.path.startsWith(path)
}
</script>

<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">S</div>
          <span class="logo-text">标注平台</span>
        </div>
      </div>

      <!-- 导航 -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 用户信息 -->
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">
            {{ userName.charAt(0).toUpperCase() }}
          </div>
          <div class="user-detail">
            <span class="user-name">{{ userName }}</span>
            <span class="user-role">{{ userRole }}</span>
          </div>
          <button class="logout-btn" @click="handleLogout" title="退出登录">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main">
      <!-- 顶部导航 -->
      <header class="header">
        <div class="breadcrumb">
          <span class="breadcrumb-item">首页</span>
          <span v-if="route.name !== 'Projects'" class="breadcrumb-separator">/</span>
          <span v-if="route.name !== 'Projects'" class="breadcrumb-item active">{{ route.meta?.title || '' }}</span>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  width: 100%;
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  min-width: 240px;
  background: #111827;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: #165DFF;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
}

.logo-text {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.nav-item.active {
  background: #165DFF;
  color: white;
}

.nav-label {
  font-weight: 500;
}

/* 用户信息 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: #165DFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.user-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.user-role {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.logout-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.5);
  background: none;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

/* 主内容区 */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.header {
  height: 56px;
  padding: 0 24px;
  background: white;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  align-items: center;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.breadcrumb-item {
  color: #6B7280;
}

.breadcrumb-item.active {
  color: #111827;
  font-weight: 500;
}

.breadcrumb-separator {
  color: #D1D5DB;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: #F9FAFB;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 60px;
    min-width: 60px;
  }

  .logo-text,
  .nav-label,
  .user-detail {
    display: none;
  }
}
</style>