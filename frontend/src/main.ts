import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 全局样式 - StepFun设计系统
import '@/assets/styles/variables.scss'

import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')