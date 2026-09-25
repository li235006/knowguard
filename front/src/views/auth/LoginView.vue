<template>
  <!-- PAGE-01: 用户统一登录与认证页 (/login) -->
  <div class="min-h-screen w-full bg-[#F8FAFC] flex flex-col justify-between items-center py-6 px-4 select-none">
    <!-- Top Web Header -->
    <header class="w-full max-w-7xl h-12 flex items-center justify-between px-6">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 bg-[#0071E3] rounded-md flex items-center justify-center text-white shadow-sm">
          <ShieldCheck :size="16" />
        </div>
        <span class="font-bold text-[15px] tracking-tight text-[#0F172A]">KnowGuard</span>
      </div>
      <div class="flex items-center gap-4 text-xs text-[#475569]">
        <button
          type="button"
          class="hover:text-[#0071E3] transition-colors"
          @click="showHelpAlert = true"
        >
          帮助中心
        </button>
      </div>
    </header>

    <!-- Center Container -->
    <main class="w-full flex-1 flex flex-col items-center justify-center px-4">
      <div
        class="w-full max-w-[440px] bg-white rounded-2xl border border-[#E5E7EB] shadow-[0_12px_36px_rgba(15,23,42,0.06)] p-10 flex flex-col gap-6 transition-all duration-300"
      >
        <!-- Card Header -->
        <div class="flex flex-col items-center gap-2 text-center">
          <div class="w-11 h-11 bg-[#0071E3] rounded-xl flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <ShieldCheck :size="24" />
          </div>
          <h1 class="text-[22px] font-semibold tracking-tight text-[#0F172A]">KnowGuard</h1>
          <p class="text-[13px] text-[#475569]">登录您的企业账户</p>
        </div>

        <!-- Error Notification Banner -->
        <div
          v-if="errorMessage"
          class="bg-red-50 border border-red-200 text-red-600 text-xs rounded-lg p-3 flex items-start gap-2"
        >
          <AlertCircle :size="15" class="shrink-0 mt-0.5" />
          <span class="flex-1">{{ errorMessage }}</span>
        </div>

        <!-- Login Form -->
        <form @submit.prevent="handleLogin" class="flex flex-col gap-4">
          <!-- Field 1: Username -->
          <div class="flex flex-col gap-1.5">
            <label for="username" class="text-[13px] font-medium text-[#0F172A]">账号 / 工号</label>
            <div
              class="h-10 bg-[#F1F5F9] rounded-lg border border-[#E5E7EB] px-3 flex items-center gap-2.5 focus-within:border-[#0071E3] focus-within:ring-2 focus-within:ring-[#0071E3]/20 transition-all"
            >
              <User :size="15" class="text-[#94A3B8] shrink-0" />
              <input
                id="username"
                v-model="loginForm.username"
                type="text"
                placeholder="请输入工号或用户名"
                class="w-full bg-transparent text-[13px] text-[#0F172A] placeholder-[#94A3B8] focus:outline-none"
                autocomplete="username"
                required
              />
            </div>
          </div>

          <!-- Field 2: Password -->
          <div class="flex flex-col gap-1.5">
            <label for="password" class="text-[13px] font-medium text-[#0F172A]">密码</label>
            <div
              class="h-10 bg-[#F1F5F9] rounded-lg border border-[#E5E7EB] px-3 flex items-center justify-between focus-within:border-[#0071E3] focus-within:ring-2 focus-within:ring-[#0071E3]/20 transition-all"
            >
              <div class="flex items-center gap-2.5 flex-1 mr-2">
                <Lock :size="15" class="text-[#94A3B8] shrink-0" />
                <input
                  id="password"
                  v-model="loginForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入登录密码"
                  class="w-full bg-transparent text-[13px] text-[#0F172A] placeholder-[#94A3B8] focus:outline-none"
                  autocomplete="current-password"
                  required
                />
              </div>
              <button
                type="button"
                class="text-[#94A3B8] hover:text-[#475569] p-1 transition-colors cursor-pointer"
                @click.stop.prevent="togglePasswordVisibility"
                tabindex="-1"
              >
                <EyeOff v-if="showPassword" :size="15" />
                <Eye v-else :size="15" />
              </button>
            </div>
          </div>

          <!-- Auxiliary Row: Remember & Forgot -->
          <div class="flex items-center justify-between text-[13px] pt-0.5">
            <label class="flex items-center gap-2 cursor-pointer select-none text-[#475569]">
              <input
                type="checkbox"
                v-model="rememberMe"
                class="w-4 h-4 rounded border-gray-300 text-[#0071E3] focus:ring-[#0071E3]"
              />
              <span>保持登录状态</span>
            </label>
            <button
              type="button"
              class="text-[#0071E3] hover:underline font-medium text-[13px]"
              @click="handleForgotPassword"
            >
              忘记密码？
            </button>
          </div>

          <!-- Primary Submit Button -->
          <button
            type="submit"
            :disabled="isSubmitting"
            class="mt-1 h-10 w-full bg-[#0071E3] hover:bg-[#0077ED] active:scale-[0.99] disabled:opacity-60 text-white font-medium text-sm rounded-lg shadow-sm shadow-[#0071E3]/30 flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <Loader2 v-if="isSubmitting" :size="16" class="animate-spin" />
            <span>{{ isSubmitting ? '正在验证身份...' : '登录' }}</span>
          </button>
        </form>
      </div>
    </main>

    <!-- Help Modal Dialog -->
    <div
      v-if="showHelpAlert"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-xl max-w-sm w-full p-6 shadow-xl border border-gray-100 flex flex-col gap-4">
        <h3 class="font-semibold text-base text-[#0F172A]">KnowGuard 认证中心帮助</h3>
        <p class="text-xs text-[#475569] leading-relaxed">
          如遇登录凭据遗失或 4D-RBAC 权限受限，请联系所在部门知识管理员或 IT 运维服务台（电话：10086 转知识中台支持）。
        </p>
        <button
          type="button"
          class="w-full py-2 bg-[#0071E3] text-white text-xs font-medium rounded-lg hover:bg-[#0077ED] transition-colors"
          @click="showHelpAlert = false"
        >
          我知道了
        </button>
      </div>
    </div>

    <!-- Page Footer -->
    <footer class="w-full flex flex-col items-center gap-1.5 py-4 text-[12px] text-[#94A3B8]">
      <p>© 2026 KnowGuard · 企业安全知识大脑</p>
      <p class="text-[#94A3B8]/80 text-[11px]">服务条款 · 隐私政策 · 安全合规</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
/**
 * 统一认证中心视图
 * 原型对应: PAGE-01 (login.png)
 * 模块: FE-M1 / P0-1
 */

import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ShieldCheck, User, Lock, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loginForm = reactive({
  username: '',
  password: ''
})

const showPassword = ref(false)
const rememberMe = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref('')
const showHelpAlert = ref(false)

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

const handleForgotPassword = () => {
  errorMessage.value = '请联系系统管理员或所在部门知识主管重置登录凭据。'
}

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    errorMessage.value = '请输入登录账号与密码'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    // 调用 Pinia store 的统一 login 动作（内聚登录 + /me 拉取与持久化）
    await authStore.login({
      username: loginForm.username.trim(),
      password: loginForm.password.trim()
    })

    // 根据角色智能重定向：普通员工默认进入问答工作台，管理员进入后台控制台
    const defaultPath = authStore.isCommonUser ? '/chat' : '/admin/knowledge/units'
    const redirectPath = (route.query.redirect as string) || defaultPath
    router.push(redirectPath)
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '网络连接失败，请确认后端或 Mock 服务状态'
  } finally {
    isSubmitting.value = false
  }
}
</script>
