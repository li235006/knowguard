"""
X-Trace-Id 全链路追踪中间件

职责:
    - 拦截所有进入系统的 HTTP 请求，提取或自动生成唯一 X-Trace-Id
    - 将 TraceId 绑定至 Request.state
    - 在响应 Header 中回写 X-Trace-Id 供前端调试与审计关联

架构定位:
    网络与中间件层 (Middlewares)

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TraceMiddleware(BaseHTTPMiddleware):
    """全链路追踪中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-Id")
        if not trace_id:
            ts = int(time.time() * 1000)
            suffix = uuid.uuid4().hex[:8]
            trace_id = f"trace-kg-{ts}-{suffix}"

        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response
