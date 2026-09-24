"""
角色与功能权限控制器 (Roles Router)

接口清单:
    - GET  /api/v1/roles: 查询所有角色列表
    - POST /api/v1/roles: 创建新角色
    - PUT  /api/v1/roles/{id}/permissions: 为角色分配菜单、路由与操作按钮权限

架构定位:
    API 控制器层 / 模块一: IAM 中心

作者:
    System Architect (系统架构组)
"""

from typing import List
from fastapi import APIRouter
from app.schemas.common import StandardResponse
from app.schemas.user import RoleCreate, RoleResponse

router = APIRouter()


@router.get("", response_model=StandardResponse[List[RoleResponse]])
async def list_roles():
    """获取角色列表存根"""
    pass


@router.post("", response_model=StandardResponse[RoleResponse])
async def create_role(payload: RoleCreate):
    """创建角色存根"""
    pass
