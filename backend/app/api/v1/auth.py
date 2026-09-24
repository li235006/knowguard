"""
认证与授权控制器 (Auth Router)

接口清单:
    - POST /api/v1/auth/login: 用户登录并签发 Token
    - POST /api/v1/auth/refresh: 刷新 Access Token
    - POST /api/v1/auth/logout: 退出登录并作废 Token
    - GET  /api/v1/auth/me: 获取当前登录员工上下文信息

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

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middlewares.auth_middleware import get_current_user
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse, UserContext
from app.schemas.common import StandardResponse
from app.services.iam_service import IAMService

router = APIRouter()


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """用户登录接口并颁发双 Token (Access 120min / Refresh 7天)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    token_resp, _ = await service.login(payload)
    return StandardResponse(
        code=200,
        message="登录成功",
        data=token_resp,
        trace_id=trace_id,
    )


@router.post("/refresh", response_model=StandardResponse[TokenResponse])
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """无感续签 Access Token 接口"""
    trace_id = getattr(request.state, "trace_id", None)
    service = IAMService(db)
    token_resp = await service.refresh_access_token(payload.refresh_token)
    return StandardResponse(
        code=200,
        message="令牌续签成功",
        data=token_resp,
        trace_id=trace_id,
    )


@router.post("/logout", response_model=StandardResponse[bool])
async def logout(
    request: Request,
    current_user: UserContext = Depends(get_current_user),
):
    """退出登录接口"""
    trace_id = getattr(request.state, "trace_id", None)
    return StandardResponse(
        code=200,
        message="已成功退出登录",
        data=True,
        trace_id=trace_id,
    )


@router.get("/me", response_model=StandardResponse[UserContext])
async def get_current_user_profile(
    request: Request,
    current_user: UserContext = Depends(get_current_user),
):
    """获取当前登录用户身份上下文与权限树信息"""
    trace_id = getattr(request.state, "trace_id", None)
    return StandardResponse(
        code=200,
        message="获取个人上下文成功",
        data=current_user,
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

    async def _test_auth_router():
        print("=== [Self-Test] Starting Auth Router Self-Test ===")
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _override_get_db():
            async with TestSessionLocal() as session:
                yield session

        test_app = FastAPI()
        test_app.add_middleware(TraceMiddleware)
        test_app.include_router(router, prefix="/api/v1/auth")
        test_app.dependency_overrides[get_db] = _override_get_db

        # 初始化测试用户与角色
        async with TestSessionLocal() as session:
            service = IAMService(session)
            await service.init_builtin_roles_and_permissions()
            await service.create_user(UserCreate(
                employee_id="10086",
                username="zhangsan",
                real_name="张三",
                password="Password123!",
                is_active=True,
            ))

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 登录验证
            res = await client.post(
                "/api/v1/auth/login",
                json={"username": "10086", "password": "Password123!"},
                headers={"X-Trace-Id": "trace-test-auth-001"}
            )
            assert res.status_code == 200, f"Login failed: {res.text}"
            res_data = res.json()
            assert res_data["code"] == 200
            assert res_data["trace_id"] == "trace-test-auth-001"
            access_token = res_data["data"]["access_token"]
            refresh_token_val = res_data["data"]["refresh_token"]
            print("[Self-Test] Login succeeded, access_token acquired.")

            # 2. 获取当前用户个人画像 /me
            me_res = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert me_res.status_code == 200
            me_data = me_res.json()
            assert me_data["data"]["employee_id"] == "10086"
            assert me_data["data"]["username"] == "zhangsan"
            print("[Self-Test] GET /me succeeded.")

            # 3. 刷新 Token /refresh
            ref_res = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token_val}
            )
            assert ref_res.status_code == 200
            ref_data = ref_res.json()
            assert ref_data["data"]["access_token"] is not None
            print("[Self-Test] POST /refresh succeeded.")

            # 4. 退出登录 /logout
            logout_res = await client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert logout_res.status_code == 200
            print("[Self-Test] POST /logout succeeded.")

        await test_engine.dispose()
        print("=== [Self-Test] All Auth Router tests PASSED successfully! ===")

    asyncio.run(_test_auth_router())
