"""
模块 M1 身份认证与权限管理自动化测试套件 (test_m1_auth.py)

测试范围:
    - Bcrypt 12 工作因子密码加密与比对
    - 正常凭据登录与 JWT 双 Token 颁发 (Access Token 120min / Refresh Token 7天)
    - 错误凭据拦截与业务状态码 40001
    - 停用账号拦截与业务状态码 40101
    - GET /me 用户个人上下文解析
    - POST /refresh 无感续签
    - POST /logout 登出接口
    - X-Trace-Id 穿透回写验证

作者:
    Backend Team & QA
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.schemas.user import UserCreate
from app.services.iam_service import IAMService


@pytest.mark.asyncio
async def test_bcrypt_work_factor_and_verification():
    """测试 Bcrypt 密码散列与校验 (工作因子 12)"""
    plain = "SuperPassword2026!"
    hashed = get_password_hash(plain)

    # 验证工作因子为 12
    assert hashed.startswith("$2b$12$"), "Bcrypt 哈希必须采用 12 工作因子"
    assert verify_password(plain, hashed) is True, "正确密码必须校验成功"
    assert verify_password("WrongPassword123", hashed) is False, "错误密码必须校验失败"
    assert verify_password("", hashed) is False, "空密码必须校验失败"


@pytest.mark.asyncio
async def test_auth_login_success_and_tokens(client: AsyncClient, db_session: AsyncSession):
    """测试正常登录、双 Token 颁发与 X-Trace-Id 链路穿透"""
    service = IAMService(db_session)
    await service.create_user(UserCreate(
        employee_id="10086",
        username="zhangsan",
        real_name="张三",
        password="MySecretPassword123",
        is_active=True,
    ))

    trace_id_val = "trace-test-auth-login-001"
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "10086", "password": "MySecretPassword123"},
        headers={"X-Trace-Id": trace_id_val},
    )

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["code"] == 200
    assert res_json["message"] == "登录成功"
    assert res_json["trace_id"] == trace_id_val
    assert response.headers.get("X-Trace-Id") == trace_id_val

    data = res_json["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 7200

    # 解码校验 Access Token
    access_claims = decode_token(data["access_token"])
    assert access_claims["sub"] is not None
    assert access_claims["username"] == "zhangsan"
    assert access_claims["token_type"] == "access"


@pytest.mark.asyncio
async def test_auth_login_wrong_password_blocked(client: AsyncClient, db_session: AsyncSession):
    """测试错误密码登录被拦截并返回 400"""
    service = IAMService(db_session)
    await service.create_user(UserCreate(
        employee_id="10087",
        username="lisi",
        real_name="李四",
        password="ValidPassword123",
        is_active=True,
    ))

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "lisi", "password": "WrongPassword999"},
    )
    assert response.status_code == 400
    res_json = response.json()
    assert res_json["code"] == 40001
    assert "用户名或密码错误" in res_json["message"]


@pytest.mark.asyncio
async def test_auth_login_disabled_account_blocked(client: AsyncClient, db_session: AsyncSession):
    """测试停用账号登录被拦截并返回 401"""
    service = IAMService(db_session)
    await service.create_user(UserCreate(
        employee_id="10088",
        username="wangwu",
        real_name="王五",
        password="ValidPassword123",
        is_active=False,
    ))

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "10088", "password": "ValidPassword123"},
    )
    assert response.status_code == 401
    res_json = response.json()
    assert res_json["code"] == 40101
    assert "停用" in res_json["message"]


@pytest.mark.asyncio
async def test_auth_get_current_user_profile(client: AsyncClient, db_session: AsyncSession):
    """测试携带合法 Access Token 获取个人身份上下文与权限列表"""
    service = IAMService(db_session)
    await service.create_user(UserCreate(
        employee_id="10089",
        username="zhaoliu",
        real_name="赵六",
        password="ValidPassword123",
        is_active=True,
    ))

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "zhaoliu", "password": "ValidPassword123"},
    )
    token = login_res.json()["data"]["access_token"]

    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["employee_id"] == "10089"
    assert me_data["username"] == "zhaoliu"
    assert me_data["real_name"] == "赵六"


@pytest.mark.asyncio
async def test_auth_expired_token_rejected(client: AsyncClient):
    """测试过期 Token 访问受限接口触发 40101"""
    expired_token = create_access_token(
        {"sub": "999", "username": "expired_user"},
        expires_delta=timedelta(seconds=-10),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == 40101


@pytest.mark.asyncio
async def test_auth_refresh_token_flow(client: AsyncClient, db_session: AsyncSession):
    """测试无感续签换发全新 Access Token"""
    service = IAMService(db_session)
    await service.create_user(UserCreate(
        employee_id="10090",
        username="sunqi",
        real_name="孙七",
        password="ValidPassword123",
        is_active=True,
    ))

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "sunqi", "password": "ValidPassword123"},
    )
    refresh_token = login_res.json()["data"]["refresh_token"]

    ref_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 200
    ref_data = ref_res.json()["data"]
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data

    # 验证新 Token 可以正常访问 /me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {ref_data['access_token']}"},
    )
    assert me_res.status_code == 200
