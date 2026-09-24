"""
组织架构与身份鉴权核心服务 (IAM Service)

职责:
    - 部门 8 级递归树构建、增删改查、物化路径编码计算与级联约束
    - 员工用户生命周期管理 (CRUD、Bcrypt 12 密码加密、状态启停用)
    - 5 大内置角色与三级 RBAC 权限分配 (菜单、路由、按钮)
    - 用户登录凭据验证、JWT 双 Token 签发与无感续签

架构定位:
    业务服务层 (Services Layer) / 模块一: IAM 中心

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    AuthenticationError,
    BusinessLogicError,
    EntityNotFoundError,
    PermissionDeniedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import Department, Role, RolePermission, User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserContext
from app.schemas.user import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeResponse,
    DepartmentUpdate,
    PermissionTreeNode,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)

# 5 大系统内置角色定义
BUILTIN_ROLES = [
    {
        "code": "ROLE_SUPER_ADMIN",
        "name": "超级管理员",
        "description": "拥有系统全量控制权限、组织架构管理、系统底层密钥与审计配置",
        "is_system": True,
    },
    {
        "code": "ROLE_KNOWLEDGE_ADMIN",
        "name": "知识管理员",
        "description": "负责知识库维护、文档导入切片、向量重构与知识自进化",
        "is_system": True,
    },
    {
        "code": "ROLE_COMMON_USER",
        "name": "普通员工",
        "description": "仅具备问答工作台、个人历史会话及放行知识查阅权限",
        "is_system": True,
    },
    {
        "code": "ROLE_HRBP",
        "name": "HRBP",
        "description": "具备人力行政知识管理、部门员工权限协同权限",
        "is_system": True,
    },
    {
        "code": "ROLE_AUDITOR",
        "name": "合规审计员",
        "description": "负责安全审计日志调阅、合规拦截监控与风险态势感知",
        "is_system": True,
    },
]

# 标准三级 RBAC 授权树模板 (菜单 ➔ 路由 ➔ 按钮)
STANDARD_PERMISSION_TREE: List[Dict[str, Any]] = [
    {
        "id": "menu:system",
        "label": "系统管理",
        "code": "system:menu",
        "type": "menu",
        "resource_path": "/admin/system",
        "children": [
            {
                "id": "route:system:dept",
                "label": "部门架构管理",
                "code": "system:dept:view",
                "type": "route",
                "resource_path": "/admin/system/departments",
                "children": [
                    {"id": "btn:dept:create", "label": "新增部门", "code": "system:dept:create", "type": "button", "resource_path": "POST /api/v1/departments"},
                    {"id": "btn:dept:update", "label": "修改部门", "code": "system:dept:update", "type": "button", "resource_path": "PUT /api/v1/departments/*"},
                    {"id": "btn:dept:delete", "label": "删除部门", "code": "system:dept:delete", "type": "button", "resource_path": "DELETE /api/v1/departments/*"},
                ],
            },
            {
                "id": "route:system:user",
                "label": "员工账号管理",
                "code": "system:user:view",
                "type": "route",
                "resource_path": "/admin/system/users",
                "children": [
                    {"id": "btn:user:create", "label": "新增员工", "code": "system:user:create", "type": "button", "resource_path": "POST /api/v1/users"},
                    {"id": "btn:user:update", "label": "修改员工", "code": "system:user:update", "type": "button", "resource_path": "PUT /api/v1/users/*"},
                    {"id": "btn:user:status", "label": "启停员工账号", "code": "system:user:status", "type": "button", "resource_path": "PATCH /api/v1/users/*/status"},
                ],
            },
            {
                "id": "route:system:role",
                "label": "角色与权限策略",
                "code": "system:role:view",
                "type": "route",
                "resource_path": "/admin/system/roles",
                "children": [
                    {"id": "btn:role:update", "label": "配置角色权限", "code": "system:role:update", "type": "button", "resource_path": "PUT /api/v1/roles/*/permissions"},
                    {"id": "btn:role:assign", "label": "分配用户角色", "code": "system:role:assign", "type": "button", "resource_path": "POST /api/v1/users/*/roles"},
                ],
            },
        ],
    },
    {
        "id": "menu:knowledge",
        "label": "知识资产管理",
        "code": "knowledge:menu",
        "type": "menu",
        "resource_path": "/admin/knowledge",
        "children": [
            {
                "id": "route:knowledge:list",
                "label": "资产检索与台账列表",
                "code": "knowledge:view",
                "type": "route",
                "resource_path": "/admin/knowledge/units",
                "children": [
                    {"id": "btn:knowledge:import", "label": "批量导入与文档上传", "code": "knowledge:import", "type": "button", "resource_path": "POST /api/v1/knowledge/upload"},
                    {"id": "btn:knowledge:reparse", "label": "分词切片重析与向量化", "code": "knowledge:reparse", "type": "button", "resource_path": "POST /api/v1/knowledge/*/reparse"},
                    {"id": "btn:knowledge:delete", "label": "物理删除销毁知识资产", "code": "knowledge:delete", "type": "button", "resource_path": "DELETE /api/v1/knowledge/*"},
                ],
            }
        ],
    },
    {
        "id": "menu:evolution",
        "label": "知识自进化中心",
        "code": "evolution:menu",
        "type": "menu",
        "resource_path": "/admin/evolution",
        "children": [
            {
                "id": "route:evolution:view",
                "label": "缺口清单与聚类审核",
                "code": "evolution:view",
                "type": "route",
                "resource_path": "/admin/evolution/gaps",
                "children": [
                    {"id": "btn:evolution:ticket", "label": "知识缺口转建工单派发", "code": "evolution:ticket:create", "type": "button", "resource_path": "POST /api/v1/evolution/tickets"},
                    {"id": "btn:faq:publish", "label": "FAQ 审核与一键发布沉淀", "code": "faq:publish", "type": "button", "resource_path": "POST /api/v1/evolution/faqs/publish"},
                ],
            }
        ],
    },
    {
        "id": "menu:analytics",
        "label": "运营监控与审计大盘",
        "code": "analytics:menu",
        "type": "menu",
        "resource_path": "/admin/analytics",
        "children": [
            {
                "id": "route:analytics:view",
                "label": "问答监控与KPI大盘查阅",
                "code": "analytics:view",
                "type": "route",
                "resource_path": "/admin/analytics/dashboard",
                "children": [
                    {"id": "btn:audit:export", "label": "导出审计流水存证报告", "code": "audit:export", "type": "button", "resource_path": "POST /api/v1/analytics/audit/export"},
                ],
            }
        ],
    },
    {
        "id": "menu:chat",
        "label": "AI 智能问答工作台",
        "code": "chat:menu",
        "type": "menu",
        "resource_path": "/chat",
        "children": [
            {
                "id": "route:chat:view",
                "label": "问答工作台访问",
                "code": "chat:view",
                "type": "route",
                "resource_path": "/chat",
                "children": [
                    {"id": "btn:chat:send", "label": "发起提问与SSE交互", "code": "chat:send", "type": "button", "resource_path": "POST /api/v1/chat/completions"},
                    {"id": "btn:chat:feedback", "label": "问答反馈打标", "code": "chat:feedback", "type": "button", "resource_path": "POST /api/v1/chat/feedback"},
                ],
            }
        ],
    },
]


class IAMService:
    """组织架构与身份鉴权服务实现"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== 初始化与种子数据 ====================

    async def init_builtin_roles_and_permissions(self) -> None:
        """初始化 5 大系统内置角色及权限体系"""
        for role_meta in BUILTIN_ROLES:
            stmt = select(Role).where(Role.code == role_meta["code"], Role.is_deleted == False)
            res = await self.db.execute(stmt)
            role = res.scalars().first()
            if not role:
                role = Role(
                    code=role_meta["code"],
                    name=role_meta["name"],
                    description=role_meta["description"],
                    is_system=True,
                    status=True,
                )
                self.db.add(role)
                await self.db.flush()

                # 为超级管理员分配全量权限
                if role.code == "ROLE_SUPER_ADMIN":
                    all_perms = self._flatten_permission_tree(STANDARD_PERMISSION_TREE)
                    for p in all_perms:
                        self.db.add(RolePermission(
                            role_id=role.id,
                            permission_code=p["code"],
                            permission_type=p["type"],
                            name=p["label"],
                            resource_path=p.get("resource_path"),
                        ))
                elif role.code == "ROLE_COMMON_USER":
                    # 普通员工仅赋予问答相关权限
                    common_perms = ["chat:menu", "chat:view", "chat:send", "chat:feedback"]
                    for p in self._flatten_permission_tree(STANDARD_PERMISSION_TREE):
                        if p["code"] in common_perms:
                            self.db.add(RolePermission(
                                role_id=role.id,
                                permission_code=p["code"],
                                permission_type=p["type"],
                                name=p["label"],
                                resource_path=p.get("resource_path"),
                            ))
        await self.db.commit()

    def _flatten_permission_tree(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """扁平化展开权限树"""
        result = []
        for node in nodes:
            result.append(node)
            if "children" in node and node["children"]:
                result.extend(self._flatten_permission_tree(node["children"]))
        return result

    # ==================== 身份认证与 Token ====================

    async def authenticate_user(self, username: str, password: str) -> User:
        """根据工号或用户名核验密码并返回用户"""
        stmt = (
            select(User)
            .where(
                (User.username == username) | (User.employee_id == username),
                User.is_deleted == False,
            )
            .options(selectinload(User.roles).selectinload(Role.permissions), selectinload(User.department))
        )
        res = await self.db.execute(stmt)
        user = res.scalars().first()

        if not user:
            raise BusinessLogicError(message="用户名或密码错误", code=40001)

        if not verify_password(password, user.hashed_password):
            raise BusinessLogicError(message="用户名或密码错误", code=40001)

        if not user.is_active:
            raise AuthenticationError(message="账号已被停用，请联系管理员", code=40101)

        return user

    async def login(self, req: LoginRequest) -> Tuple[TokenResponse, UserContext]:
        """登录并颁发双 Token (Access Token 120min / Refresh Token 7天)"""
        user = await self.authenticate_user(req.username, req.password)
        permissions = await self.get_user_permissions(user.id)
        role_ids = [r.id for r in user.roles]
        role_codes = [r.code for r in user.roles]

        claims = {
            "sub": str(user.id),
            "username": user.username,
            "real_name": user.real_name,
            "employee_id": user.employee_id,
            "dept_id": user.department_id,
            "role_ids": role_ids,
            "role_codes": role_codes,
            "permissions": permissions,
        }

        access_token = create_access_token(claims)
        refresh_token = create_refresh_token({"sub": str(user.id), "token_type": "refresh"})

        token_resp = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=7200,
        )

        user_context = UserContext(
            user_id=user.id,
            employee_id=user.employee_id,
            username=user.username,
            real_name=user.real_name,
            dept_id=user.department_id,
            dept_name=user.department.name if user.department else None,
            role_ids=role_ids,
            role_codes=role_codes,
            permissions=permissions,
            avatar=user.avatar,
            is_superuser=user.is_superuser,
        )

        return token_resp, user_context

    async def refresh_access_token(self, refresh_token_str: str) -> TokenResponse:
        """使用 Refresh Token 无感续签 Access Token"""
        payload = decode_token(refresh_token_str)
        if payload.get("token_type") != "refresh":
            raise AuthenticationError(message="非法的 Refresh Token 类型", code=40101)

        user_id = int(payload.get("sub"))
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError(message="用户不存在或已被停用", code=40101)

        permissions = await self.get_user_permissions(user.id)
        claims = {
            "sub": str(user.id),
            "username": user.username,
            "real_name": user.real_name,
            "employee_id": user.employee_id,
            "dept_id": user.department_id,
            "role_ids": [r.id for r in user.roles],
            "role_codes": [r.code for r in user.roles],
            "permissions": permissions,
        }
        new_access_token = create_access_token(claims)
        new_refresh_token = create_refresh_token({"sub": str(user.id), "token_type": "refresh"})

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=7200,
        )

    async def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户拥有的全部细粒度权限编码集合 (去重)"""
        stmt = (
            select(User)
            .where(User.id == user_id, User.is_deleted == False)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        res = await self.db.execute(stmt)
        user = res.scalars().first()
        if not user:
            return []

        # 超级管理员拥有全量权限
        if user.is_superuser:
            all_perms = self._flatten_permission_tree(STANDARD_PERMISSION_TREE)
            return list(set(p["code"] for p in all_perms))

        permissions = set()
        for role in user.roles:
            if role.code == "ROLE_SUPER_ADMIN":
                all_perms = self._flatten_permission_tree(STANDARD_PERMISSION_TREE)
                return list(set(p["code"] for p in all_perms))
            for perm in role.permissions:
                permissions.add(perm.permission_code)

        return sorted(list(permissions))

    # ==================== 部门组织架构 (8级物化路径) ====================

    async def get_department_tree(self) -> List[DepartmentTreeResponse]:
        """递归构建 8 级部门树形层级结构"""
        stmt = (
            select(Department)
            .where(Department.is_deleted == False)
            .order_by(Department.level.asc(), Department.sort_order.asc(), Department.id.asc())
        )
        res = await self.db.execute(stmt)
        all_depts = res.scalars().all()

        # 映射缓存与递归组装
        dept_map: Dict[int, DepartmentTreeResponse] = {}
        for dept in all_depts:
            dept_map[dept.id] = DepartmentTreeResponse(
                id=dept.id,
                name=dept.name,
                code=dept.code,
                parent_id=dept.parent_id,
                materialized_path=dept.materialized_path,
                level=dept.level,
                sort_order=dept.sort_order,
                leader_name=dept.leader_name,
                phone=dept.phone,
                email=dept.email,
                status=dept.status,
                created_at=dept.created_at,
                updated_at=dept.updated_at,
                children=[],
            )

        tree: List[DepartmentTreeResponse] = []
        for dept in all_depts:
            node = dept_map[dept.id]
            if dept.parent_id is None or dept.parent_id not in dept_map:
                tree.append(node)
            else:
                dept_map[dept.parent_id].children.append(node)

        return tree

    async def create_department(self, data: DepartmentCreate) -> Department:
        """新增部门节点，严格执行 8 级层级约束与物化路径编码计算"""
        # 检查部门编码全局唯一性
        stmt = select(Department).where(Department.code == data.code, Department.is_deleted == False)
        res = await self.db.execute(stmt)
        if res.scalars().first():
            raise BusinessLogicError(message=f"部门编码 '{data.code}' 已存在", code=40001)

        level = 1
        parent_path = "/"
        if data.parent_id is not None:
            parent = await self.db.get(Department, data.parent_id)
            if not parent or parent.is_deleted:
                raise EntityNotFoundError(message=f"指定的父部门 ID {data.parent_id} 不存在", code=40401)
            if parent.level >= 8:
                raise BusinessLogicError(message="系统最多支持 8 级部门树结构，当前节点已达最深层级，无法新增子部门！", code=40001)
            level = parent.level + 1
            parent_path = parent.materialized_path

        dept = Department(
            name=data.name,
            code=data.code,
            parent_id=data.parent_id,
            materialized_path=parent_path,  # 先占位
            level=level,
            sort_order=data.sort_order,
            leader_name=data.leader_name,
            phone=data.phone,
            email=data.email,
            status=data.status,
        )
        self.db.add(dept)
        await self.db.flush()

        # 生成标准物化路径: "/1/3/7/"
        dept.materialized_path = f"{parent_path}{dept.id}/" if parent_path.endswith("/") else f"{parent_path}/{dept.id}/"
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def update_department(self, dept_id: int, data: DepartmentUpdate) -> Department:
        """修改部门信息，支持调整父节点与自动级联刷新所有下属节点的物化路径"""
        dept = await self.db.get(Department, dept_id)
        if not dept or dept.is_deleted:
            raise EntityNotFoundError(message=f"部门 ID {dept_id} 不存在", code=40401)

        if data.code and data.code != dept.code:
            stmt = select(Department).where(Department.code == data.code, Department.id != dept_id, Department.is_deleted == False)
            res = await self.db.execute(stmt)
            if res.scalars().first():
                raise BusinessLogicError(message=f"部门编码 '{data.code}' 已被占用", code=40001)
            dept.code = data.code

        if data.name is not None:
            dept.name = data.name
        if data.sort_order is not None:
            dept.sort_order = data.sort_order
        if data.leader_name is not None:
            dept.leader_name = data.leader_name
        if data.phone is not None:
            dept.phone = data.phone
        if data.email is not None:
            dept.email = data.email
        if data.status is not None:
            dept.status = data.status

        # 调整所属父部门与层级
        if data.parent_id is not None and data.parent_id != dept.parent_id:
            if data.parent_id == dept.id:
                raise BusinessLogicError(message="部门父节点不能设置为自身", code=40001)

            parent = await self.db.get(Department, data.parent_id)
            if not parent or parent.is_deleted:
                raise EntityNotFoundError(message=f"父部门 ID {data.parent_id} 不存在", code=40401)

            # 环路检测: 新父节点不能位于当前部门的子树中
            if f"/{dept.id}/" in parent.materialized_path:
                raise BusinessLogicError(message="禁止将部门移动至其自身的子部门之下 (产生循环引用)", code=40001)

            # 计算子树最大深度
            sub_max_stmt = select(func.max(Department.level)).where(
                Department.materialized_path.like(f"{dept.materialized_path}%"),
                Department.is_deleted == False
            )
            sub_max_res = await self.db.execute(sub_max_stmt)
            max_child_level = sub_max_res.scalar() or dept.level
            delta_level = parent.level + 1 - dept.level
            if max_child_level + delta_level > 8:
                raise BusinessLogicError(message="移动后该分支最大深度将超过 8 级上限，操作被阻断！", code=40001)

            old_path = dept.materialized_path
            new_parent_path = parent.materialized_path
            new_path = f"{new_parent_path}{dept.id}/" if new_parent_path.endswith("/") else f"{new_parent_path}/{dept.id}/"

            dept.parent_id = parent.id
            dept.level = parent.level + 1
            dept.materialized_path = new_path

            # 级联更新所有子孙部门的路径与层级
            child_stmt = select(Department).where(
                Department.materialized_path.like(f"{old_path}%"),
                Department.id != dept.id,
                Department.is_deleted == False
            )
            child_res = await self.db.execute(child_stmt)
            for child in child_res.scalars().all():
                child.materialized_path = child.materialized_path.replace(old_path, new_path, 1)
                child.level = child.level + delta_level

        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def delete_department(self, dept_id: int) -> bool:
        """删除部门节点，非叶子节点与关联有员工的部门强制阻断删除"""
        dept = await self.db.get(Department, dept_id)
        if not dept or dept.is_deleted:
            raise EntityNotFoundError(message=f"部门 ID {dept_id} 不存在", code=40401)

        # 1. 检查是否存在未删除的下级子部门
        child_count_stmt = select(func.count(Department.id)).where(
            Department.parent_id == dept_id,
            Department.is_deleted == False
        )
        child_count_res = await self.db.execute(child_count_stmt)
        if (child_count_res.scalar() or 0) > 0:
            raise BusinessLogicError(message="该部门包含下级子部门，禁止直接删除，请先移除或转移子部门！", code=40001)

        # 2. 检查是否存在归属该部门的正常员工
        user_count_stmt = select(func.count(User.id)).where(
            User.department_id == dept_id,
            User.is_deleted == False
        )
        user_count_res = await self.db.execute(user_count_stmt)
        if (user_count_res.scalar() or 0) > 0:
            raise BusinessLogicError(message="该部门下存在关联员工账号，禁止删除，请先调岗或离职处理！", code=40001)

        dept.is_deleted = True
        dept.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    # ==================== 员工用户 CRUD ====================

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        dept_id: Optional[int] = None,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[UserResponse], int]:
        """分页检索员工列表"""
        stmt = (
            select(User)
            .where(User.is_deleted == False)
            .options(selectinload(User.roles).selectinload(Role.permissions), selectinload(User.department))
            .order_by(User.id.desc())
        )

        count_stmt = select(func.count(User.id)).where(User.is_deleted == False)

        if dept_id is not None:
            # 支持检索本部门及全部子孙部门的员工 (通过物化路径)
            dept = await self.db.get(Department, dept_id)
            if dept:
                sub_dept_ids_stmt = select(Department.id).where(
                    Department.materialized_path.like(f"{dept.materialized_path}%"),
                    Department.is_deleted == False
                )
                stmt = stmt.where(User.department_id.in_(sub_dept_ids_stmt))
                count_stmt = count_stmt.where(User.department_id.in_(sub_dept_ids_stmt))
            else:
                stmt = stmt.where(User.department_id == dept_id)
                count_stmt = count_stmt.where(User.department_id == dept_id)

        if keyword:
            kw_filter = (
                User.real_name.ilike(f"%{keyword}%")
                | User.username.ilike(f"%{keyword}%")
                | User.employee_id.ilike(f"%{keyword}%")
            )
            stmt = stmt.where(kw_filter)
            count_stmt = count_stmt.where(kw_filter)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        users = res.scalars().all()

        items = []
        for u in users:
            roles_resp = [
                RoleResponse(
                    id=r.id,
                    name=r.name,
                    code=r.code,
                    description=r.description,
                    status=r.status,
                    is_system=r.is_system,
                    permission_codes=[p.permission_code for p in r.permissions],
                )
                for r in u.roles
            ]
            items.append(UserResponse(
                id=u.id,
                employee_id=u.employee_id,
                username=u.username,
                real_name=u.real_name,
                email=u.email,
                phone=u.phone,
                avatar=u.avatar,
                department_id=u.department_id,
                department_name=u.department.name if u.department else None,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                roles=roles_resp,
                created_at=u.created_at,
                updated_at=u.updated_at,
            ))

        return items, total

    async def get_user_by_id(self, user_id: int) -> User:
        """根据 ID 获取员工实体"""
        stmt = (
            select(User)
            .where(User.id == user_id, User.is_deleted == False)
            .options(selectinload(User.roles).selectinload(Role.permissions), selectinload(User.department))
        )
        res = await self.db.execute(stmt)
        user = res.scalars().first()
        if not user:
            raise EntityNotFoundError(message=f"用户 ID {user_id} 不存在", code=40401)
        return user

    async def create_user(self, data: UserCreate) -> UserResponse:
        """创建新员工账号，密码强制使用 Bcrypt 12 工作因子哈希"""
        # 校验工号与登录名唯一性
        stmt = select(User).where(
            (User.employee_id == data.employee_id) | (User.username == data.username),
            User.is_deleted == False,
        )
        res = await self.db.execute(stmt)
        if res.scalars().first():
            raise BusinessLogicError(message=f"工号 '{data.employee_id}' 或用户名 '{data.username}' 已存在", code=40001)

        if data.department_id is not None:
            dept = await self.db.get(Department, data.department_id)
            if not dept or dept.is_deleted:
                raise EntityNotFoundError(message=f"部门 ID {data.department_id} 不存在", code=40401)

        hashed_password = get_password_hash(data.password)

        user = User(
            employee_id=data.employee_id,
            username=data.username,
            real_name=data.real_name,
            hashed_password=hashed_password,
            email=data.email,
            phone=data.phone,
            avatar=data.avatar,
            department_id=data.department_id,
            is_active=data.is_active,
            is_superuser=data.is_superuser,
        )
        self.db.add(user)
        await self.db.flush()

        # 关联角色
        if data.role_ids:
            for rid in data.role_ids:
                self.db.add(UserRole(user_id=user.id, role_id=rid))
            await self.db.flush()

        await self.db.commit()
        await self.db.refresh(user)

        user_full = await self.get_user_by_id(user.id)
        return UserResponse(
            id=user_full.id,
            employee_id=user_full.employee_id,
            username=user_full.username,
            real_name=user_full.real_name,
            email=user_full.email,
            phone=user_full.phone,
            avatar=user_full.avatar,
            department_id=user_full.department_id,
            department_name=user_full.department.name if user_full.department else None,
            is_active=user_full.is_active,
            is_superuser=user_full.is_superuser,
            roles=[
                RoleResponse(
                    id=r.id,
                    name=r.name,
                    code=r.code,
                    description=r.description,
                    status=r.status,
                    is_system=r.is_system,
                    permission_codes=[p.permission_code for p in r.permissions],
                )
                for r in user_full.roles
            ],
            created_at=user_full.created_at,
            updated_at=user_full.updated_at,
        )

    async def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        """更新员工信息或重置密码"""
        user = await self.get_user_by_id(user_id)

        if data.real_name is not None:
            user.real_name = data.real_name
        if data.email is not None:
            user.email = data.email
        if data.phone is not None:
            user.phone = data.phone
        if data.avatar is not None:
            user.avatar = data.avatar
        if "department_id" in data.model_fields_set:
            if data.department_id is not None:
                dept = await self.db.get(Department, data.department_id)
                if not dept or dept.is_deleted:
                    raise EntityNotFoundError(message=f"部门 ID {data.department_id} 不存在", code=40401)
                user.department_id = data.department_id
            else:
                user.department_id = None
        if data.password:
            user.hashed_password = get_password_hash(data.password)

        if data.role_ids is not None:
            await self.db.execute(delete(UserRole).where(UserRole.user_id == user.id))
            for rid in data.role_ids:
                self.db.add(UserRole(user_id=user.id, role_id=rid))
            await self.db.flush()

        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        user_full = await self.get_user_by_id(user.id)
        return UserResponse(
            id=user_full.id,
            employee_id=user_full.employee_id,
            username=user_full.username,
            real_name=user_full.real_name,
            email=user_full.email,
            phone=user_full.phone,
            avatar=user_full.avatar,
            department_id=user_full.department_id,
            department_name=user_full.department.name if user_full.department else None,
            is_active=user_full.is_active,
            is_superuser=user_full.is_superuser,
            roles=[
                RoleResponse(
                    id=r.id,
                    name=r.name,
                    code=r.code,
                    description=r.description,
                    status=r.status,
                    is_system=r.is_system,
                    permission_codes=[p.permission_code for p in r.permissions],
                )
                for r in user_full.roles
            ],
            created_at=user_full.created_at,
            updated_at=user_full.updated_at,
        )

    async def set_user_status(self, user_id: int, is_active: bool) -> bool:
        """启停用员工账号"""
        user = await self.get_user_by_id(user_id)
        user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    # ==================== 角色与 RBAC 权限 ====================

    async def list_roles(self) -> List[RoleResponse]:
        """获取所有角色及其权限代码列表"""
        stmt = (
            select(Role)
            .where(Role.is_deleted == False)
            .options(selectinload(Role.permissions))
            .order_by(Role.id.asc())
        )
        res = await self.db.execute(stmt)
        roles = res.scalars().all()
        return [
            RoleResponse(
                id=r.id,
                name=r.name,
                code=r.code,
                description=r.description,
                status=r.status,
                is_system=r.is_system,
                permission_codes=[p.permission_code for p in r.permissions],
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in roles
        ]

    async def create_role(self, data: RoleCreate) -> RoleResponse:
        """创建自定义业务角色"""
        stmt = select(Role).where(Role.code == data.code, Role.is_deleted == False)
        res = await self.db.execute(stmt)
        if res.scalars().first():
            raise BusinessLogicError(message=f"角色编码 '{data.code}' 已存在", code=40001)

        role = Role(
            name=data.name,
            code=data.code,
            description=data.description,
            status=data.status,
            is_system=False,
        )
        self.db.add(role)
        await self.db.flush()

        if data.permission_codes:
            flat_perms = {p["code"]: p for p in self._flatten_permission_tree(STANDARD_PERMISSION_TREE)}
            for code in data.permission_codes:
                meta = flat_perms.get(code, {"label": code, "type": "button", "resource_path": None})
                self.db.add(RolePermission(
                    role_id=role.id,
                    permission_code=code,
                    permission_type=meta["type"],
                    name=meta["label"],
                    resource_path=meta.get("resource_path"),
                ))

        await self.db.commit()
        await self.db.refresh(role)
        return RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            status=role.status,
            is_system=role.is_system,
            permission_codes=data.permission_codes,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )

    async def update_role_permissions(self, role_id: int, permission_codes: List[str]) -> RoleResponse:
        """更新角色的细粒度 RBAC 权限"""
        stmt = select(Role).where(Role.id == role_id, Role.is_deleted == False).options(selectinload(Role.permissions))
        res = await self.db.execute(stmt)
        role = res.scalars().first()
        if not role:
            raise EntityNotFoundError(message=f"角色 ID {role_id} 不存在", code=40401)

        # 清除原有权限并替换为新全量
        del_stmt = select(RolePermission).where(RolePermission.role_id == role.id)
        existing_perms_res = await self.db.execute(del_stmt)
        for ep in existing_perms_res.scalars().all():
            await self.db.delete(ep)

        flat_perms = {p["code"]: p for p in self._flatten_permission_tree(STANDARD_PERMISSION_TREE)}
        for code in permission_codes:
            meta = flat_perms.get(code, {"label": code, "type": "button", "resource_path": None})
            self.db.add(RolePermission(
                role_id=role.id,
                permission_code=code,
                permission_type=meta["type"],
                name=meta["label"],
                resource_path=meta.get("resource_path"),
            ))

        await self.db.commit()
        await self.db.refresh(role)
        return RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            status=role.status,
            is_system=role.is_system,
            permission_codes=permission_codes,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )

    def get_permission_tree(self) -> List[PermissionTreeNode]:
        """获取系统三级 RBAC 授权树模板"""
        def _build_tree(node_list: List[Dict[str, Any]]) -> List[PermissionTreeNode]:
            nodes = []
            for item in node_list:
                nodes.append(PermissionTreeNode(
                    id=item["id"],
                    label=item["label"],
                    code=item["code"],
                    type=item["type"],
                    resource_path=item.get("resource_path"),
                    children=_build_tree(item.get("children", [])),
                ))
            return nodes

        return _build_tree(STANDARD_PERMISSION_TREE)


if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.database import Base

    async def _test_iam_service_local():
        print("=== [Self-Test] Starting IAMService Self-Test ===")
        # 1. 创建异步 SQLite 内存引擎与表结构
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async with TestSessionLocal() as session:
            service = IAMService(session)

            # 2. 初始化 5 大内置角色
            await service.init_builtin_roles_and_permissions()
            roles = await service.list_roles()
            assert len(roles) >= 5, f"必须包含至少 5 个内置角色, 当前: {len(roles)}"
            role_codes = [r.code for r in roles]
            assert "ROLE_SUPER_ADMIN" in role_codes
            assert "ROLE_COMMON_USER" in role_codes
            print(f"[Self-Test] 5 Built-in roles initialized: {role_codes}")

            # 3. 部门 8 级递归树测试与物化路径校验
            root = await service.create_department(DepartmentCreate(
                name="集团总部",
                code="CORP_HQ",
                parent_id=None
            ))
            assert root.level == 1
            assert root.materialized_path == f"/{root.id}/"

            current_parent = root
            for lvl in range(2, 9):
                child = await service.create_department(DepartmentCreate(
                    name=f"第{lvl}级分支",
                    code=f"BRANCH_LVL_{lvl}",
                    parent_id=current_parent.id
                ))
                assert child.level == lvl
                assert child.materialized_path.startswith(current_parent.materialized_path)
                current_parent = child
            print("[Self-Test] Successfully created full 8 levels of departments.")

            # 验证超过 8 级时阻断
            try:
                await service.create_department(DepartmentCreate(
                    name="第9级非法部门",
                    code="BRANCH_LVL_9",
                    parent_id=current_parent.id
                ))
                raise AssertionError("Should not allow creating level 9 department!")
            except BusinessLogicError as e:
                print(f"[Self-Test] Correctly blocked 9th level department: {e.message}")

            # 验证非叶子节点删除阻断
            try:
                await service.delete_department(root.id)
                raise AssertionError("Should not allow deleting non-leaf department!")
            except BusinessLogicError as e:
                print(f"[Self-Test] Correctly blocked non-leaf dept deletion: {e.message}")

            # 4. 员工账号 CRUD 与 Bcrypt 12 密码校验
            user_resp = await service.create_user(UserCreate(
                employee_id="10086",
                username="zhangsan",
                real_name="张三",
                password="SecurePassword2026!",
                department_id=root.id,
                role_ids=[roles[0].id]
            ))
            assert user_resp.employee_id == "10086"
            print(f"[Self-Test] Created user {user_resp.real_name} with employee_id: {user_resp.employee_id}")

            # 验证登录与双 Token 颁发
            login_req = LoginRequest(username="10086", password="SecurePassword2026!")
            token_resp, user_ctx = await service.login(login_req)
            assert token_resp.access_token is not None
            assert token_resp.refresh_token is not None
            assert user_ctx.username == "zhangsan"
            print("[Self-Test] Login and dual token generation PASSED.")

            # 验证无感续签
            refreshed_tokens = await service.refresh_access_token(token_resp.refresh_token)
            assert refreshed_tokens.access_token is not None
            print("[Self-Test] Refresh token seamless renewal PASSED.")

            # 验证启停用控制
            await service.set_user_status(user_resp.id, False)
            try:
                await service.login(login_req)
                raise AssertionError("Disabled user should not be able to log in!")
            except AuthenticationError as e:
                print(f"[Self-Test] Correctly blocked disabled user login: {e.message}")

        await test_engine.dispose()
        print("=== [Self-Test] All IAMService tests PASSED successfully! ===")

    asyncio.run(_test_iam_service_local())
