"""
4D-RBAC 权限策略与安全护栏数据契约 (Guard Schemas)

职责:
    - 四维权限配置请求与详情响应模型 (全局/部门树/角色/个人)
    - 内部鉴权调用契约 (UserContext + candidate_unit_ids -> allowed / denied)

架构定位:
    数据契约层 (Schemas) / 模块三: 4D 权限与安全护栏

作者:
    System Architect (系统架构组)
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PermissionPolicyConfig(BaseModel):
    """四维权限配置请求存根"""
    is_global: bool = Field(default=False, description="是否全员公开")
    department_ids: List[int] = Field(default_factory=list, description="授权部门ID列表")
    role_ids: List[int] = Field(default_factory=list, description="授权角色ID列表")
    user_ids: List[int] = Field(default_factory=list, description="授权员工ID列表")


class PermissionPolicyResponse(PermissionPolicyConfig):
    """四维权限配置响应存根"""
    unit_id: int
    updated_at: str


class AccessCheckRequest(BaseModel):
    """动态鉴权决策计算请求存根"""
    candidate_unit_ids: List[int]


class AccessCheckResult(BaseModel):
    """动态鉴权决策计算结果存根"""
    allowed_unit_ids: List[int]
    restricted_unit_ids: List[int]
