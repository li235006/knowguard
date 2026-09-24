/**
 * KnowGuard 前端应用主入口 (Entrypoint)
 * 
 * 职责:
 *  - 初始化 Vue 3 应用实例
 *  - 安装 Pinia 状态管理
 *  - 挂载 Vue Router 路由
 *  - 注册全局自定义指令 (v-permission)
 *  - 注入全局 Tailwind 及 Apple 极简微质感样式表
 * 
 * 架构定位:
 *  前端接入层 / Application Root
 * 
 * 作者:
 *  System Architect (前端架构组)
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setupDirectives } from './directives'

import './assets/styles/tailwind.css'
import './assets/styles/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
setupDirectives(app)

app.mount('#app')
