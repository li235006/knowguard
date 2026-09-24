"""
员工账号管理控制器 (Users Router)

接口清单:
    - GET    /api/v1/users: 分页查询员工列表
    - POST   /api/v1/users: 新增员工账号
    - GET    /api/v1/users/{id}: 获取员工详情
    - PUT    /api/v1/users/{id}: 修改员工信息与部门角色绑定
    - PATCH  /api/v1/users/{id}/status: 启用/停用员工账号

架构定位:
    API 控制器层 / 模块一: IAM 中心

作者:
    System Architect (系统架构组)
"""

from fastapi import APIRouter
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.get("", response_model=StandardResponse[PaginatedResponse[UserResponse]])
async def list_users():
    """分页查询员工列表存根"""
    pass


@router.post("", response_model=StandardResponse[UserResponse])
async def create_user(payload: UserCreate):
    """新增员工账号存根"""
    pass
