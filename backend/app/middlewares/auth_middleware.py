"""
JWT 身份认证与 UserContext 绑定中间件及依赖注入项

职责:
    - 拦截除公共放行路由外的全部业务请求
    - 校验 Bearer Token 合法性
    - 构建标准化 UserContext (userId, deptId, roleIds 等) 并挂载至 Request.state
    - 提供 FastAPI 依赖注入项 get_current_user() 与 require_permissions()

架构定位:
    网络与中间件层 (Middlewares) / 认证安全

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import List, Optional
from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_token
from app.schemas.auth import UserContext

bearer_scheme = HTTPBearer(auto_error=False)

# 免鉴权公共路由白名单
WHITELIST_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 统一身份认证与上下文绑定中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 白名单接口或 OPTIONS 请求直接放行
        path = request.url.path
        if request.method == "OPTIONS" or any(path == wp or path.startswith(wp + "/") for wp in WHITELIST_PATHS):
            return await call_next(request)

        # 尝试提取 Authorization Header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = decode_token(token)
                request.state.user = payload
            except AuthenticationError:
                # 若携带了但无效，将在 endpoint Depends 时严格拦截
                request.state.user = None
        else:
            request.state.user = None

        return await call_next(request)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> UserContext:
    """FastAPI 依赖注入: 获取当前认证用户上下文"""
    token = None
    if credentials:
        token = credentials.credentials
    elif hasattr(request.state, "user") and request.state.user:
        # 已通过中间件解析
        payload = request.state.user
        return UserContext(
            user_id=int(payload.get("sub")),
            employee_id=payload.get("employee_id", ""),
            username=payload.get("username", ""),
            real_name=payload.get("real_name", payload.get("username", "")),
            dept_id=payload.get("dept_id"),
            dept_name=payload.get("dept_name"),
            role_ids=payload.get("role_ids", []),
            role_codes=payload.get("role_codes", []),
            permissions=payload.get("permissions", []),
            avatar=payload.get("avatar"),
            is_superuser=payload.get("is_superuser", False),
        )

    if not token:
        raise AuthenticationError(message="未提供认证凭据，请登录", code=40101)

    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise AuthenticationError(message="凭据类型错误，请使用 Access Token", code=40101)

    return UserContext(
        user_id=int(payload.get("sub")),
        employee_id=payload.get("employee_id", ""),
        username=payload.get("username", ""),
        real_name=payload.get("real_name", payload.get("username", "")),
        dept_id=payload.get("dept_id"),
        dept_name=payload.get("dept_name"),
        role_ids=payload.get("role_ids", []),
        role_codes=payload.get("role_codes", []),
        permissions=payload.get("permissions", []),
        avatar=payload.get("avatar"),
        is_superuser=payload.get("is_superuser", False),
    )


def require_permissions(required_codes: List[str]):
    """权限校验依赖工厂"""
    async def _permission_checker(current_user: UserContext = Depends(get_current_user)):
        if current_user.is_superuser or "ROLE_SUPER_ADMIN" in current_user.role_codes:
            return current_user

        user_perms = set(current_user.permissions)
        for code in required_codes:
            if code not in user_perms:
                raise PermissionDeniedError(message=f"缺少操作权限: {code}", code=40301)
        return current_user

    return _permission_checker
