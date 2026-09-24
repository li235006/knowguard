<template>
  <!-- FE-M0: 管理端左右布局框架 -->
  <div class="flex h-screen w-full bg-[#F8FAFC] overflow-hidden">
    <AdminSidebar />
    <div class="flex flex-col flex-1 h-full overflow-hidden min-w-0">
      <AdminHeader />
      <main class="flex-1 overflow-y-auto p-6 bg-[#F8FAFC]">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 统一管理控制台布局框架
 * 架构定位: FE-M0 / 全局公共基座
 */
import AdminSidebar from './AdminSidebar.vue'
import AdminHeader from './AdminHeader.vue'
</script>

