"""
四维细粒度数据权限策略实体模型 (PermissionPolicy)

职责:
    - 知识单元与数据访问权限的映射策略配置
    - 支撑四维实体映射: 全局公开 (is_global)、部门列表 (departments)、角色列表 (roles)、个人列表 (users)
    - 遵循 OR 充分条件裁决语义与写时展开机制

架构定位:
    持久化数据模型层 (Data Models) / 模块三: 4D 权限与安全护栏 (MySQL 8.0+)

作者:
    System Architect (系统架构组)
"""

from typing import List
from sqlalchemy import Boolean, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class PermissionPolicy(BaseModel):
    """四维细粒度权限策略实体存根 (MySQL 8.0+)"""
    __tablename__ = "permission_policies"
    pass
