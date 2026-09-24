/**
 * 知识资产维护、切片与四维权限 API
 * 模块: FE-M4 / P1-1
 * 接口契约对齐: backend/app/schemas/knowledge.py & guard.py
 * 支持真实后端 RESTful 联调与 VITE_ENABLE_MOCK=true/false 双态自由切换
 */

import request, { generateTraceId } from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type {
  KnowledgeUnit,
  ChunkItem,
  PermissionPolicyConfig
} from '@/types/knowledge'

const isMockEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_MOCK === 'true'
}

// 内存中维护可变的 Mock 知识单元数据 (PAGE-03 原型对齐)
let liveMockUnits: KnowledgeUnit[] = [
  {
    id: 1001,
    title: '2026年度企业差旅报销与补贴管理标准.pdf',
    file_type: 'PDF',
    file_size: 2516582, // 2.4 MB
    category: 'FINANCE',
    status: 'INDEXED',
    chunk_count: 48,
    permission_summary: '全员公开',
    created_at: '2026-03-20 10:15:00'
  },
  {
    id: 1002,
    title: '研发团队敏捷迭代与代码发布规范.md',
    file_type: 'MD',
    file_size: 460800, // 450 KB
    category: 'TECH',
    status: 'INDEXED',
    chunk_count: 18,
    permission_summary: '部门: 研发与技术中心',
    created_at: '2026-03-21 14:30:00'
  },
  {
    id: 1003,
    title: '企业核心高管中长期股权激励分配办法.docx',
    file_type: 'DOCX',
    file_size: 1887436, // 1.8 MB
    category: 'HR',
    status: 'INDEXED',
    chunk_count: 32,
    permission_summary: '角色: 超级管理员 / 高管',
    created_at: '2026-03-22 09:00:00'
  },
  {
    id: 1004,
    title: '2026战略合规安全保密红线白皮书.pdf',
    file_type: 'PDF',
    file_size: 3355443, // 3.2 MB
    category: 'SECURITY',
    status: 'INDEXED',
    chunk_count: 64,
    permission_summary: '全员公开',
    created_at: '2026-03-22 16:45:00'
  },
  {
    id: 1005,
    title: '分布式向量检索优化与Milvus集群部署手册.md',
    file_type: 'MD',
    file_size: 839680, // 820 KB
    category: 'TECH',
    status: 'DISABLED',
    chunk_count: 24,
    permission_summary: '部门: 基础架构工程部',
    created_at: '2026-03-23 11:20:00'
  },
  {
    id: 1006,
    title: '集团财务合规与反洗钱内部审查细则.txt',
    file_type: 'TXT',
    file_size: 317440, // 310 KB
    category: 'LEGAL',
    status: 'INDEXED',
    chunk_count: 12,
    permission_summary: '角色: 安全审计员',
    created_at: '2026-03-24 08:30:00'
  },
  {
    id: 1007,
    title: '2026半年度新员工培训入职指导手册.pdf',
    file_type: 'PDF',
    file_size: 5347737, // 5.1 MB
    category: 'HR',
    status: 'PARSING',
    chunk_count: 0,
    permission_summary: '全员公开',
    created_at: '2026-03-24 11:15:00'
  },
  {
    id: 1008,
    title: '2025集团保密协议历史归档扫描件.pdf',
    file_type: 'PDF',
    file_size: 9332326, // 8.9 MB
    category: 'SECURITY',
    status: 'FAILED',
    chunk_count: 0,
    permission_summary: '角色: 安全审计员',
    error_message: 'PDF OCR 解析超时 (ERR_TIMEOUT)',
    created_at: '2026-03-24 11:30:00'
  }
]

export interface GetKnowledgeUnitsQuery extends PaginationParams {
  category?: string
  format?: string
  status?: string
  search?: string
}

// 1. 获取知识资产列表 (分页与过滤)
export const getKnowledgeUnitsApi = async (
  params: GetKnowledgeUnitsQuery
): Promise<ApiResponse<PaginatedData<KnowledgeUnit>>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    let filtered = [...liveMockUnits]

    if (params.search && params.search.trim()) {
      const q = params.search.trim().toLowerCase()
      filtered = filtered.filter(
        (u) =>
          u.title.toLowerCase().includes(q) ||
          String(u.id).includes(q) ||
          (u.permission_summary && u.permission_summary.toLowerCase().includes(q))
      )
    }

    if (params.format && params.format !== 'ALL') {
      filtered = filtered.filter((u) => u.file_type.toUpperCase() === params.format!.toUpperCase())
    }

    if (params.category && params.category !== 'ALL') {
      filtered = filtered.filter((u) => u.category.toUpperCase() === params.category!.toUpperCase())
    }

    if (params.status && params.status !== 'ALL') {
      filtered = filtered.filter((u) => u.status.toUpperCase() === params.status!.toUpperCase())
    }

    const page = params.page || 1
    const pageSize = params.page_size || 10
    const start = (page - 1) * pageSize
    const paginatedItems = filtered.slice(start, start + pageSize)

    return {
      code: 200,
      message: 'success',
      data: {
        items: paginatedItems,
        total: filtered.length,
        page,
        page_size: pageSize
      },
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/knowledge/units', { params })
}

// 2. 上传知识文档 (multipart/form-data)
export const uploadDocumentApi = async (
  file: File,
  category: string = 'DEFAULT'
): Promise<ApiResponse<KnowledgeUnit>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 300))
    const ext = file.name.split('.').pop()?.toUpperCase() || 'TXT'
    const newUnit: KnowledgeUnit = {
      id: 1000 + liveMockUnits.length + 1,
      title: file.name,
      file_type: ext,
      file_size: file.size,
      category,
      status: 'INDEXED',
      chunk_count: Math.max(1, Math.ceil(file.size / 51200)),
      permission_summary: '全员公开',
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
    }
    liveMockUnits.unshift(newUnit)

    return {
      code: 200,
      message: '文档上传、滑动分块与向量入库成功',
      data: newUnit,
      trace_id: generateTraceId()
    }
  }

  const formData = new FormData()
  formData.append('file', file)
  formData.append('category', category)

  return request.post('/api/v1/knowledge/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 3. 启停用知识单元 (PATCH /status)
export const updateUnitStatusApi = async (
  unitId: number,
  status: string
): Promise<ApiResponse<KnowledgeUnit>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    const target = liveMockUnits.find((u) => u.id === unitId)
    if (!target) throw new Error('未找到指定知识单元')
    target.status = status
    return {
      code: 200,
      message: status === 'INDEXED' ? '知识资产已重新启用' : '知识资产已安全下线停用',
      data: target,
      trace_id: generateTraceId()
    }
  }

  return request.patch(`/api/v1/knowledge/units/${unitId}/status`, { status })
}

// 4. 物理删除知识单元 (DELETE)
export const deleteKnowledgeUnitApi = async (
  unitId: number
): Promise<ApiResponse<{ deleted_id: number }>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    liveMockUnits = liveMockUnits.filter((u) => u.id !== unitId)
    return {
      code: 200,
      message: '知识文档及切片向量已成功销毁',
      data: { deleted_id: unitId },
      trace_id: generateTraceId()
    }
  }

  return request.delete(`/api/v1/knowledge/units/${unitId}`)
}

// 5. 获取指定文档切片明细列表
export const getUnitChunksApi = async (unitId: number): Promise<ApiResponse<ChunkItem[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    const mockChunks: ChunkItem[] = [
      {
        id: 1,
        unit_id: unitId,
        chunk_index: 0,
        content: '第一章 总则与适用范围：本标准适用于集团总部及各下属分子公司正式在册员工出差管理...',
        char_length: 480,
        status: 'indexed',
        has_vector: true,
        metadata: { page: 1, section: '总则' }
      },
      {
        id: 2,
        unit_id: unitId,
        chunk_index: 1,
        content: '第二章 交通与住宿报销上限：一类城市（北上广深）住宿标准上限为 600 元/天，伙食补助包干 120 元/天...',
        char_length: 504,
        status: 'indexed',
        has_vector: true,
        metadata: { page: 14, section: '补贴标准' }
      }
    ]
    return {
      code: 200,
      message: '获取切片明细成功',
      data: mockChunks,
      trace_id: generateTraceId()
    }
  }

  return request.get(`/api/v1/knowledge/units/${unitId}/chunks`)
}

// 6. 获取与更新 4D 权限策略
export const getUnitPolicyApi = async (unitId: number): Promise<ApiResponse<PermissionPolicyConfig>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return {
      code: 200,
      message: 'success',
      data: {
        unit_id: unitId,
        is_global: unitId !== 1003 && unitId !== 1005,
        department_ids: [2, 3],
        role_ids: [1, 2],
        user_ids: []
      },
      trace_id: generateTraceId()
    }
  }

  return request.get(`/api/v1/guard/policies/${unitId}`)
}

export const updateUnitPolicyApi = async (
  unitId: number,
  data: PermissionPolicyConfig
): Promise<ApiResponse<boolean>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const target = liveMockUnits.find((u) => u.id === unitId)
    if (target) {
      target.permission_summary = data.is_global ? '全员公开' : '指定部门/角色授权'
    }
    return {
      code: 200,
      message: '4D-RBAC 权限策略已实时更新并同步 Redis 缓存',
      data: true,
      trace_id: generateTraceId()
    }
  }

  return request.put(`/api/v1/guard/policies/${unitId}`, data)
}
