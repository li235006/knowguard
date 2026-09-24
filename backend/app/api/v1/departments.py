"""
部门组织架构树控制器 (Departments Router)

接口清单:
    - GET  /api/v1/departments/tree: 获取完整 8 级部门组织架构树
    - POST /api/v1/departments: 新增部门节点 (物化路径自动计算与 8 级深度校验)
    - PUT  /api/v1/departments/{id}: 修改部门信息或调整层级关系
    - DELETE /api/v1/departments/{id}: 删除部门节点 (非叶子节点与关联员工阻断)

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
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeResponse,
    DepartmentUpdate,
)
from app.services.iam_service import IAMService

router = APIRouter()


@router.get("/tree", response_model=StandardResponse[List[DepartmentTreeResponse]])
async def get_department_tree(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """获取部门组织架构树"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    tree = await service.get_department_tree()
    return StandardResponse(
        code=200,
        message="获取部门树成功",
        data=tree,
        trace_id=trace_id,
    )


@router.post("", response_model=StandardResponse[DepartmentTreeResponse])
async def create_department(
    payload: DepartmentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """创建新部门节点"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    dept = await service.create_department(payload)
    dept_resp = DepartmentTreeResponse(
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
    return StandardResponse(
        code=200,
        message="部门创建成功",
        data=dept_resp,
        trace_id=trace_id,
    )


@router.put("/{dept_id}", response_model=StandardResponse[DepartmentResponse])
async def update_department(
    dept_id: int,
    payload: DepartmentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """修改部门信息或移动层级"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    dept = await service.update_department(dept_id, payload)
    return StandardResponse(
        code=200,
        message="部门更新成功",
        data=DepartmentResponse.model_validate(dept),
        trace_id=trace_id,
    )


@router.delete("/{dept_id}", response_model=StandardResponse[bool])
async def delete_department(
    dept_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """删除部门节点"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    result = await service.delete_department(dept_id)
    return StandardResponse(
        code=200,
        message="部门删除成功",
        data=result,
        trace_id=trace_id,
    )


if __name__ == "__main__":
    import asyncio
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.database import Base
    from app.middlewares.trace_middleware import TraceMiddleware
    from app.schemas.user import UserCreate

    async def _test_departments_router():
        print("=== [Self-Test] Starting Departments Router Self-Test ===")
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _override_get_db():
            async with TestSessionLocal() as session:
                yield session

        test_app = FastAPI()
        test_app.add_middleware(TraceMiddleware)
        test_app.include_router(router, prefix="/api/v1/departments")
        test_app.dependency_overrides[get_db] = _override_get_db

        # 准备认证上下文
        admin_user_ctx = UserContext(
            user_id=1,
            employee_id="ADMIN001",
            username="admin",
            real_name="超级管理员",
            role_ids=[1],
            role_codes=["ROLE_SUPER_ADMIN"],
            permissions=["system:dept:view", "system:dept:create", "system:dept:delete"],
            is_superuser=True,
        )
        test_app.dependency_overrides[get_current_user] = lambda: admin_user_ctx

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 创建根部门
            post_res = await client.post(
                "/api/v1/departments",
                json={"name": "集团总部", "code": "CORP_HQ", "parent_id": None},
                headers={"X-Trace-Id": "trace-test-dept-001"}
            )
            assert post_res.status_code == 200
            root_id = post_res.json()["data"]["id"]
            assert post_res.json()["data"]["level"] == 1
            print(f"[Self-Test] Created root department ID: {root_id}")

            # 2. 创建二级子部门
            sub_res = await client.post(
                "/api/v1/departments",
                json={"name": "市场部", "code": "DEPT_MKT", "parent_id": root_id}
            )
            assert sub_res.status_code == 200
            sub_id = sub_res.json()["data"]["id"]
            assert sub_res.json()["data"]["level"] == 2
            print(f"[Self-Test] Created sub department ID: {sub_id}")

            # 3. 查询部门架构树
            tree_res = await client.get("/api/v1/departments/tree")
            assert tree_res.status_code == 200
            tree_data = tree_res.json()["data"]
            assert len(tree_data) == 1
            assert len(tree_data[0]["children"]) == 1
            print("[Self-Test] GET /departments/tree verified.")

            # 4. 删除叶子节点
            del_sub_res = await client.delete(f"/api/v1/departments/{sub_id}")
            assert del_sub_res.status_code == 200
            print("[Self-Test] DELETE leaf department succeeded.")

        await test_engine.dispose()
        print("=== [Self-Test] All Departments Router tests PASSED successfully! ===")

    asyncio.run(_test_departments_router())
