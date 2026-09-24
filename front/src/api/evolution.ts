/**
 * 知识自进化、FAQ 审核与缺口工单 API
 * 模块: FE-M5 / M5: Evolution
 * 严格对齐后端 StandardResponse 契约规范与 Axios 响应拦截器解包机制
 * 支持 VITE_ENABLE_MOCK=true/false 双态自由切换
 */

import request, { generateTraceId } from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type {
  FaqCandidate,
  FaqItem,
  KnowledgeGap,
  CandidateApprovePayload,
  CandidateRejectPayload,
  FaqCreatePayload,
  FaqUpdatePayload,
  KnowledgeGapConvertPayload,
  ClusterMiningResult,
  EvolutionMetrics
} from '@/types/evolution'

const isMockEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_MOCK === 'true'
}

// 预置可变 Mock 数据副本
let liveMockCandidates: FaqCandidate[] = [
  {
    id: 1,
    cluster_id: 'cluster-001',
    cluster_count: 24,
    suggested_question: '如何申请年假与法定带薪休假？',
    suggested_answer: '员工可通过企业 OA 考勤系统提交年假申请，经直属上级审批后生效。入职满 1 年享 5 天法定年假，司龄每增加 1 年递增 1 天，上限 15 天。',
    confidence_score: 0.96,
    status: 'PENDING',
    similar_queries: ['年假怎么休', '请年假流程', '年假有多少天', '带薪假申请规范'],
    created_at: '2026-09-24 09:30:00'
  },
  {
    id: 2,
    cluster_id: 'cluster-002',
    cluster_count: 19,
    suggested_question: '差旅机酒发票报销时限与审批节点？',
    suggested_answer: '出差结束后 15 个自然日内在报销系统提交流水，附带电子发票行程单与差旅总结，部门负责人及财务审核通过后 3 个工作日内打款。',
    confidence_score: 0.94,
    status: 'PENDING',
    similar_queries: ['报销发票过期还能报吗', '出差报销需要哪些凭证', '差旅报销多久到账'],
    created_at: '2026-09-24 10:15:00'
  },
  {
    id: 3,
    cluster_id: 'cluster-003',
    cluster_count: 15,
    suggested_question: '开发环境生产数据库只读从库只读账号申请规范？',
    suggested_answer: '需在安全审计中心发起《敏感数据访问申请单》，明确查询用途与脱敏级别，经安全合规专员和技术总监双重审批后下发为期 7 天的临时访问凭据。',
    confidence_score: 0.93,
    status: 'PENDING',
    similar_queries: ['申请数据库只读权限', '查看生产从库数据申请', '数据库提权申请'],
    created_at: '2026-09-23 15:40:00'
  },
  {
    id: 4,
    cluster_id: 'cluster-004',
    cluster_count: 11,
    suggested_question: '新员工入职入网及办公笔记本领用须知？',
    suggested_answer: '入职首日上午在 IT 服务台凭工牌办理领用，统一安装企业安全加固代理与合规证书，默认分配办公网 WiFi 与内网邮箱。',
    confidence_score: 0.91,
    status: 'PENDING',
    similar_queries: ['领电脑找谁', '办公电脑领用流程', '入职配什么电脑'],
    created_at: '2026-09-23 11:20:00'
  },
  {
    id: 5,
    cluster_id: 'cluster-005',
    cluster_count: 9,
    suggested_question: '公积金异地转移与跨省封存接续操作指引？',
    suggested_answer: '请在全国住房公积金微信小程序提交“转移接续”申请，填报转出地与转入地中心名称，系统将在 5 个工作日内自动办结资金划转。',
    confidence_score: 0.89,
    status: 'PENDING',
    similar_queries: ['公积金转移', '公积金怎么转外省', '离职公积金封存'],
    created_at: '2026-09-22 17:10:00'
  },
  {
    id: 6,
    cluster_id: 'cluster-006',
    cluster_count: 7,
    suggested_question: '企业弹性工时考勤打卡补充申诉规则？',
    suggested_answer: '每月允许最多 3 次忘打卡申诉，需在次日 18:00 前由本人发起异常说明并由主管邮件核准。打卡时间窗口为 08:30 - 10:00 至 17:30 - 19:00。',
    confidence_score: 0.88,
    status: 'PENDING',
    similar_queries: ['补卡规则', '忘记打卡怎么办', '考勤申诉限制'],
    created_at: '2026-09-22 09:00:00'
  }
]

let liveMockPublishedFaqs: FaqItem[] = [
  {
    id: 101,
    standard_question: '什么是 KnowGuard 企业知识治理平台？',
    standard_answer: 'KnowGuard 是一站式企业级自进化知识库与智能问答安全网关平台，提供文档解析、多层权限隔离、实时意图防护、语义聚类挖掘与前置高速缓存等全栈能力。',
    category: '产品介绍',
    similar_questions: ['KnowGuard 是干什么的', '平台核心功能有哪些', '产品定位'],
    hit_count: 1284,
    is_cached: true,
    is_enabled: true,
    status: true,
    created_at: '2026-09-01 10:00:00'
  },
  {
    id: 102,
    standard_question: '企业年金缴纳基数与比例如何计算？',
    standard_answer: '企业年金按上年度员工月均工资基数缴纳，企业缴存比例为 4%，员工个人缴存比例为 1.5%，按月直接汇缴至受托托管账户。',
    category: '薪酬福利',
    similar_questions: ['年金扣多少', '公司交多少年金', '年金比例'],
    hit_count: 896,
    is_cached: true,
    is_enabled: true,
    status: true,
    created_at: '2026-09-05 14:20:00'
  },
  {
    id: 103,
    standard_question: '跨国远程办公网络 VPN 客户端如何配置与登录？',
    standard_answer: '请从 IT 软件中心下载官方定制版 VPN 客户端，使用统一 LDAP 工号登录，并配合手机端动态两步认证（2FA）验证码完成鉴权。',
    category: 'IT运维',
    similar_questions: ['外网连公司内网', '远程办公VPN', 'VPN双因子认证'],
    hit_count: 672,
    is_cached: true,
    is_enabled: true,
    status: true,
    created_at: '2026-09-10 09:30:00'
  },
  {
    id: 104,
    standard_question: '跨境电商海关出口申报违禁品与限制出境物资目录？',
    standard_answer: '依据海关总署最新管制通告，禁止出境物品包括易燃易爆危化品、未经检疫动植物标本及国家限制外汇贵金属，详细目录见《出口管制物资分类索引2026版》。',
    category: '合规风控',
    similar_questions: ['出海哪些东西不能发', '清关违禁品清单', '出口受限物品'],
    hit_count: 451,
    is_cached: false,
    is_enabled: true,
    status: true,
    created_at: '2026-09-15 16:45:00'
  },
  {
    id: 105,
    standard_question: '企业专利发明与软著技术申报奖金激励政策？',
    standard_answer: '发明专利初审合格奖励 5,000 元，正式授权后奖励 15,000 元；软件著作权登记完成奖励 2,000 元。由技术委员会每季度统一评议公示并随薪发放。',
    category: '技术创新',
    similar_questions: ['写软著有钱吗', '专利奖励政策', '发明专利激励'],
    hit_count: 312,
    is_cached: true,
    is_enabled: false,
    status: false,
    created_at: '2026-09-18 11:10:00'
  }
]

let liveMockKnowledgeGaps: KnowledgeGap[] = [
  {
    id: 1,
    gap_code: 'GAP-2024-001',
    query_text: '东南亚跨境关税税率及清关延误预警',
    hit_count: 18,
    domain: '跨境电商与供应链',
    department_name: '跨境电商部、供应链部',
    severity: 'P1',
    status: 'OPEN',
    reason: '知识库中缺少东南亚新关税清单文档',
    first_seen_at: '2026-09-23 10:15',
    created_at: '2026-09-23 10:15'
  },
  {
    id: 2,
    gap_code: 'GAP-2024-002',
    query_text: '2024秋季校招差旅补贴住宿上限金额',
    hit_count: 12,
    domain: '财务与差旅中心',
    department_name: '财务部',
    severity: 'P2',
    status: 'OPEN',
    reason: '校招差旅专项文件未归档上传',
    first_seen_at: '2026-09-23 11:20',
    created_at: '2026-09-23 11:20'
  },
  {
    id: 3,
    gap_code: 'GAP-2024-003',
    query_text: 'AI 模型训练私有化集群 GPU 申请流程',
    hit_count: 9,
    domain: '研发基础架构部',
    department_name: '研发部',
    severity: 'P2',
    status: 'OPEN',
    reason: '私有算力调度手册仅在内网 Wiki 暂未同步知识库',
    first_seen_at: '2026-09-22 16:40',
    created_at: '2026-09-22 16:40'
  },
  {
    id: 4,
    gap_code: 'GAP-2024-004',
    query_text: '离职公积金封存与转移跨省办理细则',
    hit_count: 8,
    domain: '人力资源中心',
    department_name: '人力资源部',
    severity: 'P3',
    status: 'OPEN',
    reason: '跨省公积金接续政策发生变更需要补充',
    first_seen_at: '2026-09-22 14:10',
    created_at: '2026-09-22 14:10'
  },
  {
    id: 5,
    gap_code: 'GAP-2024-005',
    query_text: '东南亚海外仓滞港费免收宽限期标准',
    hit_count: 6,
    domain: '跨境电商与供应链',
    department_name: '跨境电商部',
    severity: 'P2',
    status: 'CONVERTED',
    reason: '海外仓免租期细则已下发工单补充中',
    first_seen_at: '2026-09-21 18:30',
    created_at: '2026-09-21 18:30'
  }
]

// 1. 获取高频候选 FAQ 列表
export const getFaqCandidatesApi = async (
  params: PaginationParams & { status?: string; search?: string; keyword?: string }
): Promise<ApiResponse<PaginatedData<FaqCandidate>>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    let filtered = [...liveMockCandidates]
    if (params.status && params.status !== 'ALL') {
      filtered = filtered.filter((c) => c.status === params.status)
    }
    const kw = params.search || params.keyword
    if (kw && kw.trim()) {
      const q = kw.trim().toLowerCase()
      filtered = filtered.filter(
        (c) =>
          c.suggested_question.toLowerCase().includes(q) ||
          c.suggested_answer.toLowerCase().includes(q) ||
          (c.similar_queries && c.similar_queries.some((sq) => sq.toLowerCase().includes(q)))
      )
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

  const queryParams: Record<string, unknown> = {
    page: params.page || 1,
    page_size: params.page_size || 10
  }
  if (params.status && params.status !== 'ALL') queryParams.status = params.status
  const kw = params.search || params.keyword
  if (kw && kw.trim()) queryParams.keyword = kw.trim()

  return request.get('/api/v1/evolution/candidates', { params: queryParams })
}

// 2. 采纳候选 FAQ 为正式标准问答 (POST /api/v1/evolution/candidates/{id}/approve)
export const approveCandidateApi = async (
  candidateId: number,
  payload: CandidateApprovePayload
): Promise<ApiResponse<FaqItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const cand = liveMockCandidates.find((c) => c.id === candidateId)
    if (cand) {
      cand.status = 'ACCEPTED'
    }
    const newFaq: FaqItem = {
      id: Date.now(),
      standard_question: payload.standard_question || cand?.suggested_question || '未命名问题',
      standard_answer: payload.standard_answer || cand?.suggested_answer || '未命名回答',
      category: payload.category || '通用',
      similar_questions: payload.similar_questions || cand?.similar_queries || [],
      hit_count: cand?.cluster_count || 1,
      is_cached: payload.is_cached !== false,
      is_enabled: true,
      status: true,
      candidate_id: candidateId,
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
    }
    liveMockPublishedFaqs.unshift(newFaq)
    return {
      code: 200,
      message: '候选 FAQ 已成功采纳并发布至正式问答库',
      data: newFaq,
      trace_id: generateTraceId()
    }
  }

  return request.post(`/api/v1/evolution/candidates/${candidateId}/approve`, payload)
}

// 3. 驳回候选 FAQ (POST /api/v1/evolution/candidates/{id}/reject)
export const rejectCandidateApi = async (
  candidateId: number,
  payload?: CandidateRejectPayload
): Promise<ApiResponse<boolean>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    const cand = liveMockCandidates.find((c) => c.id === candidateId)
    if (cand) {
      cand.status = 'REJECTED'
    }
    return {
      code: 200,
      message: '候选 FAQ 已驳回',
      data: true,
      trace_id: generateTraceId()
    }
  }

  return request.post(`/api/v1/evolution/candidates/${candidateId}/reject`, payload || {})
}

// 4. 触发历史提问语义聚类挖掘 (POST /api/v1/evolution/cluster-mining)
export const triggerClusterMiningApi = async (
  params?: { similarity_threshold?: number; min_frequency?: number }
): Promise<ApiResponse<ClusterMiningResult>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 400))
    return {
      code: 200,
      message: '聚类挖掘完成，成功挖掘 2 个高频问题新候选簇',
      data: {
        mined_clusters: 2,
        total_queries_analyzed: 148,
        candidates_created: 2,
        candidates_updated: 0
      },
      trace_id: generateTraceId()
    }
  }

  return request.post('/api/v1/evolution/cluster-mining', params || {
    similarity_threshold: 0.88,
    min_frequency: 2
  })
}

// 5. 获取已发布 FAQ 列表 (GET /api/v1/evolution/faqs)
export const getPublishedFaqsApi = async (
  params: PaginationParams & { category?: string; search?: string; keyword?: string; is_enabled?: boolean }
): Promise<ApiResponse<PaginatedData<FaqItem>>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    let filtered = [...liveMockPublishedFaqs]
    if (params.category && params.category !== 'ALL') {
      filtered = filtered.filter((f) => f.category === params.category)
    }
    if (params.is_enabled !== undefined) {
      filtered = filtered.filter((f) => f.is_enabled === params.is_enabled)
    }
    const kw = params.search || params.keyword
    if (kw && kw.trim()) {
      const q = kw.trim().toLowerCase()
      filtered = filtered.filter(
        (f) =>
          f.standard_question.toLowerCase().includes(q) ||
          f.standard_answer.toLowerCase().includes(q) ||
          f.similar_questions.some((sq) => sq.toLowerCase().includes(q))
      )
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

  const queryParams: Record<string, unknown> = {
    page: params.page || 1,
    page_size: params.page_size || 10
  }
  if (params.category && params.category !== 'ALL') queryParams.category = params.category
  if (params.is_enabled !== undefined) queryParams.is_enabled = params.is_enabled
  const kw = params.search || params.keyword
  if (kw && kw.trim()) queryParams.keyword = kw.trim()

  return request.get('/api/v1/evolution/faqs', { params: queryParams })
}

// 6. 手动直接发布 FAQ 并预热缓存 (POST /api/v1/evolution/faqs/publish)
export const publishFaqApi = async (data: FaqCreatePayload): Promise<ApiResponse<FaqItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const newFaq: FaqItem = {
      id: Date.now(),
      standard_question: data.standard_question,
      standard_answer: data.standard_answer,
      category: data.category || '通用',
      similar_questions: data.similar_questions || [],
      hit_count: 0,
      is_cached: data.is_cached !== false,
      is_enabled: data.is_enabled !== false,
      status: data.is_enabled !== false,
      candidate_id: data.candidate_id || null,
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
    }
    liveMockPublishedFaqs.unshift(newFaq)
    return {
      code: 200,
      message: 'FAQ 发布成功，缓存已预热',
      data: newFaq,
      trace_id: generateTraceId()
    }
  }

  return request.post('/api/v1/evolution/faqs/publish', data)
}

// 7. 更新已发布 FAQ (PUT /api/v1/evolution/faqs/{id})
export const updateFaqApi = async (
  faqId: number,
  data: FaqUpdatePayload
): Promise<ApiResponse<FaqItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    const target = liveMockPublishedFaqs.find((f) => f.id === faqId)
    if (!target) throw new Error('未找到指定 FAQ 记录')
    if (data.standard_question !== undefined) target.standard_question = data.standard_question
    if (data.standard_answer !== undefined) target.standard_answer = data.standard_answer
    if (data.category !== undefined) target.category = data.category
    if (data.similar_questions !== undefined) target.similar_questions = data.similar_questions
    if (data.is_cached !== undefined) target.is_cached = data.is_cached
    if (data.is_enabled !== undefined) {
      target.is_enabled = data.is_enabled
      target.status = data.is_enabled
    }
    target.updated_at = new Date().toISOString().replace('T', ' ').substring(0, 19)
    return {
      code: 200,
      message: 'FAQ 更新成功',
      data: target,
      trace_id: generateTraceId()
    }
  }

  return request.put(`/api/v1/evolution/faqs/${faqId}`, data)
}

// 8. 启停用 FAQ (PATCH /api/v1/evolution/faqs/{id}/status)
export const toggleFaqStatusApi = async (
  faqId: number,
  isEnabled: boolean
): Promise<ApiResponse<FaqItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    const target = liveMockPublishedFaqs.find((f) => f.id === faqId)
    if (!target) throw new Error('未找到指定 FAQ 记录')
    target.is_enabled = isEnabled
    target.status = isEnabled
    return {
      code: 200,
      message: isEnabled ? 'FAQ 已启用' : 'FAQ 已停用维护',
      data: target,
      trace_id: generateTraceId()
    }
  }

  return request.patch(`/api/v1/evolution/faqs/${faqId}/status`, { is_enabled: isEnabled })
}

// 9. 启停用极速缓存直出开关 (PATCH /api/v1/evolution/faqs/{id}/cache)
export const toggleFaqCacheApi = async (
  faqId: number,
  isCached: boolean
): Promise<ApiResponse<FaqItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    const target = liveMockPublishedFaqs.find((f) => f.id === faqId)
    if (!target) throw new Error('未找到指定 FAQ 记录')
    target.is_cached = isCached
    return {
      code: 200,
      message: isCached ? '极速缓存直出已开启' : '极速缓存直出已关闭',
      data: target,
      trace_id: generateTraceId()
    }
  }

  return request.patch(`/api/v1/evolution/faqs/${faqId}/cache`, { is_cached: isCached })
}

// 10. 删除 FAQ (DELETE /api/v1/evolution/faqs/{id})
export const deleteFaqApi = async (faqId: number): Promise<ApiResponse<boolean>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    const idx = liveMockPublishedFaqs.findIndex((f) => f.id === faqId)
    if (idx !== -1) {
      liveMockPublishedFaqs.splice(idx, 1)
    }
    return {
      code: 200,
      message: 'FAQ 已删除',
      data: true,
      trace_id: generateTraceId()
    }
  }

  return request.delete(`/api/v1/evolution/faqs/${faqId}`)
}

// 11. 获取知识盲区缺口池 (GET /api/v1/evolution/gaps)
export const getKnowledgeGapsApi = async (
  params: PaginationParams & {
    status?: string
    search?: string
    keyword?: string
    sort_by?: string
    order?: string
  }
): Promise<ApiResponse<PaginatedData<KnowledgeGap>>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    let filtered = [...liveMockKnowledgeGaps]
    if (params.status && params.status !== 'ALL') {
      const targetStatus = params.status.toUpperCase()
      if (targetStatus === 'RESOLVED') {
        filtered = filtered.filter((g) => g.status === 'RESOLVED' || g.status === 'CONVERTED')
      } else if (targetStatus === 'IGNORED') {
        filtered = filtered.filter((g) => g.status === 'IGNORED' || g.status === 'DISMISSED')
      } else {
        filtered = filtered.filter((g) => g.status === targetStatus)
      }
    }
    const kw = params.search || params.keyword
    if (kw && kw.trim()) {
      const q = kw.trim().toLowerCase()
      filtered = filtered.filter(
        (g) =>
          g.query_text.toLowerCase().includes(q) ||
          (g.gap_code && g.gap_code.toLowerCase().includes(q)) ||
          (g.domain && g.domain.toLowerCase().includes(q))
      )
    }

    // 排序逻辑
    const sortBy = params.sort_by || 'hit_count'
    const isAsc = params.order?.toLowerCase() === 'asc'
    filtered.sort((a, b) => {
      let valA: number = 0
      let valB: number = 0
      if (sortBy === 'hit_count') {
        valA = a.hit_count
        valB = b.hit_count
      } else if (sortBy === 'created_at') {
        valA = new Date(a.created_at || a.first_seen_at || 0).getTime()
        valB = new Date(b.created_at || b.first_seen_at || 0).getTime()
      } else {
        valA = a.id
        valB = b.id
      }
      return isAsc ? valA - valB : valB - valA
    })

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

  const queryParams: Record<string, unknown> = {
    page: params.page || 1,
    page_size: params.page_size || 10
  }
  if (params.status && params.status !== 'ALL') queryParams.status = params.status
  if (params.sort_by) queryParams.sort_by = params.sort_by
  if (params.order) queryParams.order = params.order
  const kw = params.search || params.keyword
  if (kw && kw.trim()) queryParams.keyword = kw.trim()

  return request.get('/api/v1/evolution/gaps', { params: queryParams })
}

// 12. 知识缺口一键转建为补充工单 (POST /api/v1/evolution/gaps/{id}/convert)
export const convertKnowledgeGapApi = async (
  gapId: number,
  payload: KnowledgeGapConvertPayload
): Promise<ApiResponse<KnowledgeGap>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const gap = liveMockKnowledgeGaps.find((g) => g.id === gapId)
    if (gap) {
      gap.status = 'CONVERTED'
    }
    return {
      code: 200,
      message: '工单下发成功，已通知责任人排期编制',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: (gap || { id: gapId, status: 'CONVERTED', query_text: payload.title || '' }) as any,
      trace_id: generateTraceId()
    }
  }

  return request.post(`/api/v1/evolution/gaps/${gapId}/convert`, payload)
}

// 13. 标记知识缺口为已解决 (POST /api/v1/evolution/gaps/{id}/resolve)
export const resolveKnowledgeGapApi = async (gapId: number): Promise<ApiResponse<KnowledgeGap>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    const gap = liveMockKnowledgeGaps.find((g) => g.id === gapId)
    if (gap) {
      gap.status = 'RESOLVED'
    }
    return {
      code: 200,
      message: '知识缺口已标记解决',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: (gap || { id: gapId, status: 'RESOLVED', query_text: '' }) as any,
      trace_id: generateTraceId()
    }
  }

  return request.post(`/api/v1/evolution/gaps/${gapId}/resolve`)
}

// 14. 忽略/驳回知识缺口 (POST /api/v1/evolution/gaps/{id}/ignore)
export const ignoreKnowledgeGapApi = async (gapId: number): Promise<ApiResponse<KnowledgeGap>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    const gap = liveMockKnowledgeGaps.find((g) => g.id === gapId)
    if (gap) {
      gap.status = 'IGNORED'
    }
    return {
      code: 200,
      message: '知识缺口已忽略',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: (gap || { id: gapId, status: 'IGNORED', query_text: '' }) as any,
      trace_id: generateTraceId()
    }
  }

  return request.post(`/api/v1/evolution/gaps/${gapId}/ignore`)
}

// 13. 获取知识自进化看板核心度量统计 (GET /api/v1/evolution/metrics)
export const getEvolutionMetricsApi = async (): Promise<ApiResponse<EvolutionMetrics>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    const pendingCandidates = liveMockCandidates.filter((c) => c.status === 'PENDING').length
    const openGaps = liveMockKnowledgeGaps.filter((g) => g.status === 'OPEN').length
    return {
      code: 200,
      message: 'success',
      data: {
        unresolved_gaps_count: openGaps || 14,
        unresolved_gaps_delta: '↑ 3个 本周新增',
        pending_candidates_count: pendingCandidates || 8,
        clustering_accuracy: '94.2%',
        avg_resolution_days: 1.8,
        resolution_speedup_percent: 35
      },
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/evolution/metrics')
}
