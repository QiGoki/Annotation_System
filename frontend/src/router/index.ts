/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/user/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/tasks',  // 默认重定向到任务列表，在路由守卫中根据角色调整
    meta: { requiresAuth: true },
    children: [
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/project/ProjectList.vue'),
        meta: { title: '项目管理' },
      },
      {
        path: 'projects/create',
        name: 'ProjectCreate',
        component: () => import('@/views/project/ProjectCreate.vue'),
        meta: { title: '创建项目', requiresAdmin: true },
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/project/ProjectDetail.vue'),
        meta: { title: '项目详情' },
      },
      {
        path: 'projects/:id/configure',
        name: 'ProjectConfigure',
        component: () => import('@/views/project/ProjectConfigurator.vue'),
        meta: { title: '标注页面配置', requiresAdmin: true },
      },
      {
        path: 'projects/:id/import',
        name: 'TaskImport',
        component: () => import('@/views/task/TaskImport.vue'),
        meta: { title: '数据导入', requiresAdmin: true },
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/task/TaskList.vue'),
        meta: { title: '任务列表' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/user/UserList.vue'),
        meta: { title: '用户管理', requiresAdmin: true },
      },
    ],
  },
  // 独立布局的标注页面（不包含主网页的侧边栏和头部）
  {
    path: '/projects/:id/preview',
    name: 'AnnotationPreview',
    component: () => import('@/views/annotation/AnnotationRunner.vue'),
    meta: { title: '标注页面预览', requiresAdmin: true },
  },
  {
    path: '/annotate/:id',
    name: 'Annotation',
    component: () => import('@/views/annotation/AnnotationRunner.vue'),
    meta: { title: '标注执行' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()

  // 初始化用户状态
  if (!userStore.token) {
    userStore.initUser()
  }

  // 需要认证的路由
  if (to.meta.requiresAuth && !userStore.token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 需要管理员权限的路由
  if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    next({ name: 'Tasks' })  // 非管理员重定向到任务列表
    return
  }

  // 已登录用户访问登录页，重定向到首页
  if (to.name === 'Login' && userStore.token) {
    // 根据角色重定向
    const redirectPath = userStore.user?.role === 'admin' ? '/projects' : '/tasks'
    next(redirectPath)
    return
  }

  // 访问根路径时，根据角色重定向
  if (to.path === '/' && userStore.token) {
    const redirectPath = userStore.user?.role === 'admin' ? '/projects' : '/tasks'
    next(redirectPath)
    return
  }

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 标注平台` : '标注平台'

  next()
})

export default router
