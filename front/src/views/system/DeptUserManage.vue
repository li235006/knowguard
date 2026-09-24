<template>
  <!-- PAGE-05-A: 部门架构树与员工台账视图 (system_admin.png) -->
  <div class="h-full flex flex-col gap-4">
    <!-- Top Segmented Tabs & Title Bar -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base font-bold text-[#0F172A] tracking-tight">组织与系统设置</h2>
        <p class="text-xs text-[#64748B]">维护企业多级部门组织架构树与员工账号生命周期</p>
      </div>

      <!-- Segmented Tabs (PAGE-05 原型对齐) -->
      <div class="h-8 bg-[#F1F5F9] p-0.5 rounded-lg flex items-center gap-1 border border-[#E2E8F0]">
        <router-link
          to="/admin/system/departments"
          class="h-7 px-3 rounded-md text-xs font-semibold flex items-center transition-all bg-white text-[#0071E3] shadow-sm"
        >
          组织架构与员工
        </router-link>
        <router-link
          to="/admin/system/roles"
          class="h-7 px-3 rounded-md text-xs font-medium flex items-center transition-all text-[#64748B] hover:text-[#0F172A]"
        >
          角色与功能权限
        </router-link>
      </div>
    </div>

    <!-- Main Split Content: Left DeptTree + Right UserTable -->
    <div class="flex-1 flex gap-4 min-h-0">
      <DeptTree
        :nodes="systemStore.departmentTree"
        :selected-dept-id="systemStore.selectedDeptId"
        @select="handleSelectDept"
        @refresh="refreshData"
      />
      <UserTable
        :users="systemStore.users"
        :total="systemStore.totalUsers"
        :selected-dept-id="systemStore.selectedDeptId"
        @toggle-status="handleToggleStatus"
        @search="handleSearchUsers"
        @page-change="handlePageChange"
        @refresh="refreshData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 组织部门与员工台账管理视图
 * 原型对应: PAGE-05-A (system_admin.png)
 * 模块: FE-M3
 */

import { onMounted } from 'vue'
import { useSystemStore } from '@/stores/system'
import DeptTree from '@/components/System/DeptTree.vue'
import UserTable from '@/components/System/UserTable.vue'

const systemStore = useSystemStore()

const refreshData = async () => {
  await systemStore.fetchDepartmentTree()
  await systemStore.fetchUsers()
}

const handleSelectDept = (deptId: number | null) => {
  systemStore.selectDepartment(deptId)
}

const handleToggleStatus = async (userId: number, isActive: boolean) => {
  await systemStore.toggleUserStatus(userId, isActive)
}

const handleSearchUsers = (keyword: string) => {
  systemStore.fetchUsers({ search: keyword, page: 1 })
}

const handlePageChange = (page: number) => {
  systemStore.fetchUsers({ page })
}

onMounted(() => {
  refreshData()
})
</script>

