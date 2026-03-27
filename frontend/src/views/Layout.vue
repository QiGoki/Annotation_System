<script setup lang="ts">
/**
 * 布局组件
 */
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const userName = computed(() => userStore.user?.username || '')
const userRole = computed(() => userStore.user?.role === 'admin' ? '管理员' : '标注员')

const handleLogout = async () => {
  await userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const navItems = computed(() => {
  const items: { path: string; label: string }[] = []

  // 管理员显示项目管理
  if (userStore.user?.role === 'admin') {
    items.push({ path: '/projects', label: '项目管理' })
  }

  // 所有人都显示任务列表
  items.push({ path: '/tasks', label: '任务列表' })

  // 管理员显示用户管理
  if (userStore.user?.role === 'admin') {
    items.push({ path: '/users', label: '用户管理' })
  }

  return items
})
</script>

<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <h2>标注平台</h2>
      </div>
      <nav class="nav-menu">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="active"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶部导航 -->
      <header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name !== 'Projects'">
              {{ route.meta?.title || '' }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <span class="user-info">
            {{ userName }} ({{ userRole }})
          </span>
          <el-button link type="danger" @click="handleLogout">退出</el-button>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 220px;
  background: #001529;
  display: flex;
  flex-direction: column;

  .logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid #002140;

    h2 {
      color: #fff;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .nav-menu {
    flex: 1;
    padding: 16px 0;

    .nav-item {
      display: block;
      padding: 12px 24px;
      color: rgba(255, 255, 255, 0.65);
      text-decoration: none;
      transition: all 0.3s;

      &:hover {
        color: #fff;
        background: rgba(255, 255, 255, 0.1);
      }

      &.active {
        color: #fff;
        background: #1890ff;
      }
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 64px;
  padding: 0 24px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;

    .user-info {
      color: #666;
    }
  }
}

.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: #f0f2f5;
}
</style>
