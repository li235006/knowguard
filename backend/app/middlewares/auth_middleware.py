"""
JWT 身份认证与 UserContext 绑定中间件

职责:
    - 拦截除公共放行路由外的全部业务请求
    - 校验 Bearer Token 合法性与 Redis 黑名单/登出状态
    - 构建标准化 UserContext (userId, deptId, roleIds 等) 并挂载至 Request.state

架构定位:
    网络与中间件层 (Middlewares)

作者:
    System Architect (系统架构组)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 统一身份认证与上下文绑定中间件存根"""

    async def dispatch(self, request: Request, call_next) -> Response:
        pass
