<template>
  <!-- PAGE-05-B: 角色与权限策略视图 (role_permissions.png) -->
  <div class="h-full flex flex-col gap-4 relative overflow-hidden">
    <!-- Top Segmented Tabs & Title Bar -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h2 class="text-base font-bold text-[#0F172A] tracking-tight">角色与功能权限策略</h2>
        <p class="text-xs text-[#64748B]">管理预置业务角色与三级 RBAC（菜单 ➔ 路由 ➔ 按钮）授权策略树</p>
      </div>

      <!-- Segmented Tabs (PAGE-05 原型对齐) -->
      <div class="h-8 bg-[#F1F5F9] p-0.5 rounded-lg flex items-center gap-1 border border-[#E2E8F0]">
        <router-link
          to="/admin/system/departments"
          class="h-7 px-3 rounded-md text-xs font-medium flex items-center transition-all text-[#64748B] hover:text-[#0F172A]"
        >
          组织架构与员工
        </router-link>
        <router-link
          to="/admin/system/roles"
          class="h-7 px-3 rounded-md text-xs font-semibold flex items-center transition-all bg-white text-[#0071E3] shadow-sm"
        >
          角色与功能权限
        </router-link>
      </div>
    </div>

    <!-- Main Content Area: Role Table + Right Docked Permission Drawer -->
    <div class="flex-1 flex gap-4 min-h-0 relative overflow-hidden">
      <!-- Role Table -->
      <RoleTable
        :roles="systemStore.roles"
        :selected-role-id="selectedRole?.id || null"
        @configure-permissions="handleConfigurePermissions"
        @refresh="refreshData"
      />

      <!-- Right Permission Tree Drawer -->
      <PermissionTreeDrawer
        :is-open="drawerOpen"
        :role="selectedRole"
        :permission-tree="systemStore.permissionTree"
        @close="drawerOpen = false"
        @save="handleSavePermissions"
      />
    </div>

    <!-- Success Toast Notification -->
    <div
      v-if="toastMessage"
      class="fixed bottom-6 right-6 bg-[#0F172A] text-white text-xs px-4 py-2.5 rounded-lg shadow-xl flex items-center gap-2 z-50 animate-bounce"
    >
      <CheckCircle2 :size="15" class="text-emerald-400" />
      <span>{{ toastMessage }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 角色与功能权限配置视图
 * 原型对应: PAGE-05-B (role_permissions.png)
 * 模块: FE-M3
 */

import { ref, onMounted } from 'vue'
import { CheckCircle2 } from 'lucide-vue-next'
import { useSystemStore } from '@/stores/system'
import type { RoleItem } from '@/types/system'
import RoleTable from '@/components/System/RoleTable.vue'
import PermissionTreeDrawer from '@/components/System/PermissionTreeDrawer.vue'

const systemStore = useSystemStore()
const drawerOpen = ref(false)
const selectedRole = ref<RoleItem | null>(null)
const toastMessage = ref('')

const refreshData = async () => {
  await systemStore.fetchRoles()
  await systemStore.fetchPermissionTree()
  if (selectedRole.value) {
    const updated = systemStore.roles.find((r) => r.id === selectedRole.value!.id)
    if (updated) selectedRole.value = updated
  }
}

const handleConfigurePermissions = (role: RoleItem) => {
  selectedRole.value = role
  drawerOpen.value = true
}

const handleSavePermissions = async (roleId: number, permissions: string[]) => {
  await systemStore.updateRolePermissions(roleId, permissions)
  showToast('权限策略已实时保存并对已绑定用户生效！')
  await refreshData()
}

const showToast = (msg: string) => {
  toastMessage.value = msg
  setTimeout(() => {
    toastMessage.value = ''
  }, 2500)
}

onMounted(async () => {
  await refreshData()
  // 默认选中第一个角色并打开抽屉以完美还原 PAGE-05-B 原型状态
  if (systemStore.roles.length > 0) {
    selectedRole.value = systemStore.roles[1] || systemStore.roles[0]
    drawerOpen.value = true
  }
})
</script>

