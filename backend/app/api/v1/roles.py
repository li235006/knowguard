"""
角色与功能权限控制器 (Roles Router)

接口清单:
    - GET  /api/v1/roles: 查询所有角色列表及权限代码
    - POST /api/v1/roles: 创建自定义业务角色
    - PUT  /api/v1/roles/{id}/permissions: 为角色分配菜单、路由与操作按钮权限
    - GET  /api/v1/roles/permissions/tree: 获取系统三级 RBAC 授权树模板

架构定位:
    API 控制器层 / 模块一: IAM 中心

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middlewares.auth_middleware import get_current_user
from app.schemas.auth import UserContext
from app.schemas.common import StandardResponse
from app.schemas.user import (
    PermissionTreeNode,
    RoleCreate,
    RolePermissionUpdate,
    RoleResponse,
    RoleUpdate,
)
from app.services.iam_service import IAMService

router = APIRouter()


@router.get("", response_model=StandardResponse[List[RoleResponse]])
async def list_roles(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """获取所有角色列表及其绑定的权限代码 (包含 5 大内置业务角色)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    roles = await service.list_roles()
    return StandardResponse(
        code=200,
        message="查询角色列表成功",
        data=roles,
        trace_id=trace_id,
    )


@router.post("", response_model=StandardResponse[RoleResponse])
async def create_role(
    payload: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """创建自定义业务角色"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    role_resp = await service.create_role(payload)
    return StandardResponse(
        code=200,
        message="角色创建成功",
        data=role_resp,
        trace_id=trace_id,
    )


@router.put("/{role_id}", response_model=StandardResponse[RoleResponse])
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """修改角色基本信息或权限"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    role_resp = await service.update_role(role_id, payload)
    return StandardResponse(
        code=200,
        message="角色修改成功",
        data=role_resp,
        trace_id=trace_id,
    )


@router.put("/{role_id}/permissions", response_model=StandardResponse[RoleResponse])
async def update_role_permissions(
    role_id: int,
    payload: RolePermissionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """更新角色三级 RBAC 细粒度操作权限 (支持 permission_codes 与 permissions 别名)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    role_resp = await service.update_role_permissions(role_id, payload.get_codes())
    return StandardResponse(
        code=200,
        message="角色权限配置成功",
        data=role_resp,
        trace_id=trace_id,
    )


@router.get("/permissions/tree", response_model=StandardResponse[List[PermissionTreeNode]])
async def get_permission_tree(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """获取系统标准三级 RBAC 授权树模板 (菜单 ➔ 路由 ➔ 按钮)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    tree = service.get_permission_tree()
    return StandardResponse(
        code=200,
        message="获取权限树成功",
        data=tree,
        trace_id=trace_id,
    )



if __name__ == "__main__":
    import asyncio
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.database import Base
    from app.middlewares.trace_middleware import TraceMiddleware

    async def _test_roles_router():
        print("=== [Self-Test] Starting Roles Router Self-Test ===")
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _override_get_db():
            async with TestSessionLocal() as session:
                yield session

        test_app = FastAPI()
        test_app.add_middleware(TraceMiddleware)
        test_app.include_router(router, prefix="/api/v1/roles")
        test_app.dependency_overrides[get_db] = _override_get_db

        admin_user_ctx = UserContext(
            user_id=1,
            employee_id="ADMIN001",
            username="admin",
            real_name="超级管理员",
            role_ids=[1],
            role_codes=["ROLE_SUPER_ADMIN"],
            permissions=["system:role:view", "system:role:update"],
            is_superuser=True,
        )
        test_app.dependency_overrides[get_current_user] = lambda: admin_user_ctx

        async with TestSessionLocal() as session:
            service = IAMService(session)
            await service.init_builtin_roles_and_permissions()

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 查询角色列表 (校验 5 大内置业务角色)
            list_res = await client.get("/api/v1/roles", headers={"X-Trace-Id": "trace-test-role-001"})
            assert list_res.status_code == 200
            roles_data = list_res.json()["data"]
            codes = [r["code"] for r in roles_data]
            assert "ROLE_SUPER_ADMIN" in codes
            assert "ROLE_KNOWLEDGE_ADMIN" in codes
            assert "ROLE_DEPT_MANAGER" in codes
            assert "ROLE_EMPLOYEE" in codes
            assert "ROLE_AUDITOR" in codes
            print(f"[Self-Test] GET /roles verified: 5 builtin roles verified in {len(roles_data)} roles.")

            # 2. 查询权限树
            tree_res = await client.get("/api/v1/roles/permissions/tree")
            assert tree_res.status_code == 200
            assert len(tree_res.json()["data"]) > 0
            print("[Self-Test] GET /roles/permissions/tree verified.")

            # 3. 创建自定义角色
            create_res = await client.post(
                "/api/v1/roles",
                json={
                    "name": "财务专员",
                    "code": "ROLE_FINANCE",
                    "description": "负责财务报销核算",
                    "permission_codes": ["knowledge:view"]
                }
            )
            assert create_res.status_code == 200
            new_role_id = create_res.json()["data"]["id"]
            print(f"[Self-Test] Created role ID: {new_role_id}")

            # 4. 更新权限 (支持 permissions 别名)
            perm_res = await client.put(
                f"/api/v1/roles/{new_role_id}/permissions",
                json={"permissions": ["knowledge:view", "knowledge:import"]}
            )
            assert perm_res.status_code == 200
            assert len(perm_res.json()["data"]["permission_codes"]) == 2
            print("[Self-Test] PUT /roles/{id}/permissions verified.")

            # 5. 修改角色基本信息 (PUT /roles/{id})
            update_res = await client.put(
                f"/api/v1/roles/{new_role_id}",
                json={"name": "资深财务专家", "description": "负责集团财务审计核算"}
            )
            assert update_res.status_code == 200
            assert update_res.json()["data"]["name"] == "资深财务专家"
            print("[Self-Test] PUT /roles/{id} update verified.")

        await test_engine.dispose()
        print("=== [Self-Test] All Roles Router tests PASSED successfully! ===")

    asyncio.run(_test_roles_router())

