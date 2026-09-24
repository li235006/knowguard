"""
部门组织架构树控制器 (Departments Router)

接口清单:
    - GET  /api/v1/departments/tree: 获取完整部门组织架构树
    - POST /api/v1/departments: 新增部门节点
    - PUT  /api/v1/departments/{id}: 修改部门信息或调整层级关系
    - DELETE /api/v1/departments/{id}: 删除部门节点

架构定位:
    API 控制器层 / 模块一: IAM 中心

作者:
    System Architect (系统架构组)
"""

from typing import List
from fastapi import APIRouter
from app.schemas.common import StandardResponse
from app.schemas.user import DepartmentCreate, DepartmentTreeResponse

router = APIRouter()


@router.get("/tree", response_model=StandardResponse[List[DepartmentTreeResponse]])
async def get_department_tree():
    """获取部门组织架构树存根"""
    pass


@router.post("", response_model=StandardResponse[DepartmentTreeResponse])
async def create_department(payload: DepartmentCreate):
    """创建部门节点存根"""
    pass
