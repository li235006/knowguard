"""
员工账号管理控制器 (Users Router)

接口清单:
    - GET    /api/v1/users: 分页查询员工列表 (支持部门/姓名/工号及状态筛选)
    - POST   /api/v1/users: 新增员工账号 (Bcrypt 12 密码加密)
    - GET    /api/v1/users/{id}: 获取员工详情
    - PUT    /api/v1/users/{id}: 修改员工信息与部门角色绑定
    - PATCH  /api/v1/users/{id}/status: 启用/停用员工账号

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

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middlewares.auth_middleware import get_current_user
from app.schemas.auth import UserContext
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.iam_service import IAMService

router = APIRouter()


@router.get("", response_model=StandardResponse[PaginatedResponse[UserResponse]])
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页记录数"),
    dept_id: Optional[int] = Query(None, description="部门过滤ID"),
    keyword: Optional[str] = Query(None, description="关键字 (姓名/工号/用户名)"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """分页查询员工列表"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    items, total = await service.list_users(
        page=page,
        page_size=page_size,
        dept_id=dept_id,
        keyword=keyword,
        is_active=is_active,
    )
    return StandardResponse(
        code=200,
        message="查询员工列表成功",
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
        trace_id=trace_id,
    )


@router.post("", response_model=StandardResponse[UserResponse])
async def create_user(
    payload: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """新增员工账号"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    user_resp = await service.create_user(payload)
    return StandardResponse(
        code=200,
        message="员工账号创建成功",
        data=user_resp,
        trace_id=trace_id,
    )


@router.get("/{user_id}", response_model=StandardResponse[UserResponse])
async def get_user_detail(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """获取员工详情"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    u = await service.get_user_by_id(user_id)
    return StandardResponse(
        code=200,
        message="获取员工详情成功",
        data=UserResponse.model_validate(u),
        trace_id=trace_id,
    )


@router.put("/{user_id}", response_model=StandardResponse[UserResponse])
async def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """修改员工信息或角色绑定"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    user_resp = await service.update_user(user_id, payload)
    return StandardResponse(
        code=200,
        message="员工信息修改成功",
        data=user_resp,
        trace_id=trace_id,
    )


@router.patch("/{user_id}/status", response_model=StandardResponse[bool])
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """启用或停用员工账号"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    res = await service.set_user_status(user_id, payload.get_is_active())
    return StandardResponse(
        code=200,
        message="账号状态更新成功",
        data=res,
        trace_id=trace_id,
    )


@router.post("/{user_id}/reset-password", response_model=StandardResponse[UserResponse])
async def reset_user_password(
    user_id: int,
    payload: Optional[UserUpdate] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """重置员工账号登录密码"""
    pwd = (payload.password if payload and payload.password else None) or "KnowGuard@2026"
    trace_id = getattr(request.state, "trace_id", None) if request else None
    service = IAMService(db)
    user_resp = await service.update_user(user_id, UserUpdate(password=pwd))
    return StandardResponse(
        code=200,
        message=f"员工密码重置成功，新密码已生效: {pwd}",
        data=user_resp,
        trace_id=trace_id,
    )


if __name__ == "__main__":
    import asyncio
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.database import Base
    from app.middlewares.trace_middleware import TraceMiddleware

    async def _test_users_router():
        print("=== [Self-Test] Starting Users Router Self-Test ===")
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _override_get_db():
            async with TestSessionLocal() as session:
                yield session

        test_app = FastAPI()
        test_app.add_middleware(TraceMiddleware)
        test_app.include_router(router, prefix="/api/v1/users")
        test_app.dependency_overrides[get_db] = _override_get_db

        admin_user_ctx = UserContext(
            user_id=1,
            employee_id="ADMIN001",
            username="admin",
            real_name="超级管理员",
            role_ids=[1],
            role_codes=["ROLE_SUPER_ADMIN"],
            permissions=["system:user:view", "system:user:create", "system:user:status"],
            is_superuser=True,
        )
        test_app.dependency_overrides[get_current_user] = lambda: admin_user_ctx

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 创建员工
            create_res = await client.post(
                "/api/v1/users",
                json={
                    "employee_id": "10086",
                    "username": "zhangsan",
                    "real_name": "张三",
                    "password": "Password123!",
                    "is_active": True,
                },
                headers={"X-Trace-Id": "trace-test-user-001"}
            )
            assert create_res.status_code == 200
            user_id = create_res.json()["data"]["id"]
            print(f"[Self-Test] Created user ID: {user_id}")

            # 2. 分页查询
            list_res = await client.get("/api/v1/users?page=1&page_size=10&keyword=张三")
            assert list_res.status_code == 200
            assert list_res.json()["data"]["total"] == 1
            print("[Self-Test] GET /users pagination verified.")

            # 3. 停用账号
            status_res = await client.patch(f"/api/v1/users/{user_id}/status", json={"is_active": False})
            assert status_res.status_code == 200
            assert status_res.json()["data"] is True
            print("[Self-Test] PATCH /users/{id}/status verified.")

        await test_engine.dispose()
        print("=== [Self-Test] All Users Router tests PASSED successfully! ===")

    asyncio.run(_test_users_router())
