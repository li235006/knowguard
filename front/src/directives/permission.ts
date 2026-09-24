/**
 * v-permission 按钮级 RBAC 权限判定指令
 * 职责: 根据用户权限列表动态显示或移除 DOM 元素
 */

import type { Directive, DirectiveBinding } from 'vue'
import { useAuthStore } from '@/stores/auth'

export const permissionDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding<string | string[]>) {
    const { value } = binding
    if (!value) return

    const authStore = useAuthStore()

    let hasPerm = false
    if (Array.isArray(value)) {
      hasPerm = authStore.hasAnyPermission(value)
    } else if (typeof value === 'string') {
      hasPerm = authStore.hasPermission(value)
    }

    if (!hasPerm) {
      el.parentNode?.removeChild(el)
    }
  },
  updated(el: HTMLElement, binding: DirectiveBinding<string | string[]>) {
    const { value } = binding
    if (!value) return

    const authStore = useAuthStore()

    let hasPerm = false
    if (Array.isArray(value)) {
      hasPerm = authStore.hasAnyPermission(value)
    } else if (typeof value === 'string') {
      hasPerm = authStore.hasPermission(value)
    }

    if (!hasPerm) {
      el.parentNode?.removeChild(el)
    }
  }
}
