"""
X-Trace-Id 全链路追踪中间件

职责:
    - 拦截所有进入系统的 HTTP 请求，提取或自动生成唯一 X-Trace-Id
    - 将 TraceId 绑定至 OpenTelemetry 上下文及 Request.state
    - 在响应 Header 中回写 X-Trace-Id 供前端调试与审计关联

架构定位:
    网络与中间件层 (Middlewares)

作者:
    System Architect (系统架构组)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TraceMiddleware(BaseHTTPMiddleware):
    """全链路追踪中间件存根"""

    async def dispatch(self, request: Request, call_next) -> Response:
        pass
