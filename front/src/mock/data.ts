import type { DepartmentNode, UserItem, RoleItem, PermissionNode } from '@/types/system'

export const mockDepartments: DepartmentNode[] = [
  {
    id: 1,
    name: '管理层',
    parent_id: null,
    path: '/1',
    level: 1,
    member_count: 5,
    children: [
      {
        id: 2,
        name: '研发部',
        parent_id: 1,
        path: '/1/2',
        level: 2,
        member_count: 24,
        children: []
      },
      {
        id: 3,
        name: '财务部',
        parent_id: 1,
        path: '/1/3',
        level: 2,
        member_count: 8,
        children: []
      },
      {
        id: 4,
        name: '综合管理部',
        parent_id: 1,
        path: '/1/4',
        level: 2,
        member_count: 6,
        children: []
      }
    ]
  }
]

export const mockUsers: UserItem[] = [
  {
    id: 1,
    username: 'zhangsan',
    real_name: '张三',
    dept_id: 2,
    dept_name: '研发部',
    role_ids: [3],
    role_names: ['普通员工'],
    is_active: true,
    email: 'zhangsan@knowguard.com',
    phone: '13800000001',
    created_at: '2026-09-01T08:00:00Z'
  },
  {
    id: 2,
    username: 'lisi',
    real_name: '李四',
    dept_id: 3,
    dept_name: '财务部',
    role_ids: [2],
    role_names: ['部门经理'],
    is_active: true,
    email: 'lisi@knowguard.com',
    phone: '13800000002',
    created_at: '2026-09-01T08:00:00Z'
  },
  {
    id: 3,
    username: 'wangwu',
    real_name: '王五',
    dept_id: 1,
    dept_name: '管理层',
    role_ids: [1],
    role_names: ['超级管理员'],
    is_active: true,
    email: 'wangwu@knowguard.com',
    phone: '13800000003',
    created_at: '2026-09-01T08:00:00Z'
  }
]

export const mockRoles: RoleItem[] = [
  {
    id: 1,
    role_name: '超级管理员',
    role_code: 'ROLE_SUPER_ADMIN',
    description: '系统最高管理权限',
    user_count: 1,
    permissions: ['*']
  },
  {
    id: 2,
    role_name: '部门经理',
    role_code: 'ROLE_DEPT_MANAGER',
    description: '部门内知识管理与审批权限',
    user_count: 1,
    permissions: ['knowledge:view', 'knowledge:upload', 'chat:view', 'chat:send']
  },
  {
    id: 3,
    role_name: '普通员工',
    role_code: 'ROLE_COMMON_USER',
    description: '仅具备问答工作台与个人会话权限',
    user_count: 1,
    permissions: ['chat:view', 'chat:send']
  }
]

export const mockPermissionTree: PermissionNode[] = [
  {
    id: 'p_chat',
    code: 'chat:menu',
    title: '智能问答',
    type: 'menu',
    parent_id: null,
    children: [
      {
        id: 'p_chat_view',
        code: 'chat:view',
        title: '进入工作台',
        type: 'button',
        parent_id: 'p_chat'
      },
      {
        id: 'p_chat_send',
        code: 'chat:send',
        title: '发起提问',
        type: 'button',
        parent_id: 'p_chat'
      }
    ]
  },
  {
    id: 'p_sys',
    code: 'system:menu',
    title: '系统管理',
    type: 'menu',
    parent_id: null,
    children: [
      {
        id: 'p_sys_dept',
        code: 'system:dept:manage',
        title: '组织部门管理',
        type: 'button',
        parent_id: 'p_sys'
      },
      {
        id: 'p_sys_user',
        code: 'system:user:manage',
        title: '员工用户管理',
        type: 'button',
        parent_id: 'p_sys'
      }
    ]
  }
]

