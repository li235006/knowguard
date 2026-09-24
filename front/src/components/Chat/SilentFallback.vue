<template>
  <!-- FE-M2: 静默温和未命中展示组件 (PAGE-02 越权降级) -->
  <div
    class="w-full bg-white rounded-xl border border-[#E5E7EB] p-4 flex flex-col gap-2.5 text-xs text-[#475569] shadow-sm select-none"
  >
    <div class="flex items-center gap-1.5 text-amber-600 font-medium">
      <ShieldAlert :size="14" />
      <span>企业知识大脑安全提示</span>
    </div>

    <div class="flex flex-col gap-1.5 leading-relaxed text-[#475569]">
      <p>抱歉，在您当前授权的企业知识库范围内，未检索到相关规章或政策文档。</p>
      <p class="text-[11px] text-[#64748B]">
        建议您确认问题描述是否准确，或向所在业务主管及人力行政部门咨询相关业务指引。
      </p>
    </div>

    <div
      class="mt-1 pt-2 border-t border-[#F1F5F9] flex items-center justify-between text-[10px] text-[#94A3B8]"
    >
      <div class="flex items-center gap-1">
        <Lock :size="11" />
        <span>4D-RBAC 动态鉴权护栏生效中 (敏感知识切片已物理剔除)</span>
      </div>
      <span class="font-mono">Silent Fallback</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 静默温和未命中展示组件 (越权降级兜底)
 * 模块: FE-M2 (PAGE-02)
 */

import { ShieldAlert, Lock } from 'lucide-vue-next'
</script>
