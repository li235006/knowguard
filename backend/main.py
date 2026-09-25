"""
KnowGuard 智能知识库管理平台 - FastAPI 应用主入口

职责:
    - 初始化并配置 FastAPI Application 实例
    - 挂载生命周期上下文管理 (Lifespan: 数据库连接池、Redis 连接池初始化与销毁)
    - 挂载全系统 HTTP 中间件 (CORS, TraceId, Auth)
    - 注册聚合 API 路由 (/api/v1)
    - 注册统一全局异常处理器 (KnowGuardException, ValidationError, 500)

架构定位:
    应用接入层 / Entrypoint

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.exceptions import KnowGuardException
from app.middlewares.auth_middleware import AuthMiddleware
from app.middlewares.trace_middleware import TraceMiddleware
from app.services.iam_service import IAMService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """系统生命周期管理: 启动时连接池预热及关闭时资源优雅释放"""
    # 自动初始化 ORM 数据表与内置角色 (仅在未初始化时)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            service = IAMService(session)
            await service.init_builtin_roles_and_permissions()
            # 预热加载数据库既有切片至 Milvus (解决 InMemory 模式 0 召回缺陷)
            from app.core.milvus import milvus_service
            await milvus_service.warm_up_from_database(session)
    except Exception as e:
        # 在纯单元测试或未启动 MySQL 容器时降级
        pass

    yield

    # 关闭时清理连接池
    await engine.dispose()


def create_app() -> FastAPI:
    """创建并配置 FastAPI 核心应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # 1. 挂载跨域 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
        allow_origin_regex=r"^https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Trace-Id"],
    )

    # 2. 挂载链路追踪中间件
    app.add_middleware(TraceMiddleware)

    # 3. 挂载身份认证中间件
    app.add_middleware(AuthMiddleware)

    # 4. 全局业务异常处理器 (KnowGuardException)
    @app.exception_handler(KnowGuardException)
    async def knowguard_exception_handler(request: Request, exc: KnowGuardException):
        trace_id = getattr(request.state, "trace_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": exc.details if exc.details else None,
                "trace_id": trace_id,
            },
            headers={"X-Trace-Id": trace_id} if trace_id else {},
        )

    # 5. 请求参数校验异常处理器 (Pydantic / RequestValidationError)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = getattr(request.state, "trace_id", None)
        errors = exc.errors()
        msg = "请求参数校验未通过: " + "; ".join(f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in errors)
        return JSONResponse(
            status_code=400,
            content={
                "code": 40001,
                "message": msg,
                "data": errors,
                "trace_id": trace_id,
            },
            headers={"X-Trace-Id": trace_id} if trace_id else {},
        )

    # 6. 未捕获通用异常处理器 (500 脱敏)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        trace_id = getattr(request.state, "trace_id", None)
        return JSONResponse(
            status_code=500,
            content={
                "code": 50001,
                "message": "系统繁忙，请联系管理员",
                "data": None,
                "trace_id": trace_id,
            },
            headers={"X-Trace-Id": trace_id} if trace_id else {},
        )

    # 7. 注册聚合 API 路由
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "service": "KnowGuard Core Backend"}

    return app


app = create_app()
