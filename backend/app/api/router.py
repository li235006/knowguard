"""
KnowGuard API 统一路由汇聚与版本注册器

职责:
    - 聚合注册 V1 版本全部领域路由模块 (/api/v1)
    - 挂载认证、用户、部门、角色、知识、鉴权、问答、进化及大盘审计路由

架构定位:
    API 接入层 / 路由聚合器

作者:
    System Architect (系统架构组)
"""

from fastapi import APIRouter
from app.api.v1 import (
    analytics,
    auth,
    chat,
    departments,
    evolution,
    guard,
    knowledge,
    roles,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth & 认证"])
api_router.include_router(users.router, prefix="/users", tags=["Users & 员工管理"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments & 部门架构"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles & 角色权限"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge & 知识资产"])
api_router.include_router(guard.router, prefix="/guard", tags=["Guard & 4D安全护栏"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & 智能问答"])
api_router.include_router(evolution.router, prefix="/evolution", tags=["Evolution & 知识自进化"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & 运营审计大盘"])
