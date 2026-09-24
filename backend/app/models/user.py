"""
组织架构与身份鉴权实体模型 (User, Department, Role, RolePermission)

职责:
    - 部门树形层级模型 (Department): 8 级部门树、层级路径、父子关联
    - 用户账号模型 (User): 工号、姓名、部门外键、密码散列密文、启停用状态
    - 角色定义模型 (Role): 系统角色定义 (超级管理员、安全审计员等)
    - 角色权限映射模型 (RolePermission): 菜单级、路由级与按钮操作级 RBAC 映射表

架构定位:
    持久化数据模型层 (Data Models) / 模块一: IAM 中心

作者:
    System Architect (系统架构组)
"""

from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Department(BaseModel):
    """部门组织实体存根"""
    __tablename__ = "departments"
    pass


class Role(BaseModel):
    """角色定义实体存根"""
    __tablename__ = "roles"
    pass


class RolePermission(BaseModel):
    """角色与权限映射实体存根"""
    __tablename__ = "role_permissions"
    pass


class User(BaseModel):
    """用户员工实体存根"""
    __tablename__ = "users"
    pass


class UserRole(BaseModel):
    """用户与角色多对多关联实体存根"""
    __tablename__ = "user_roles"
    pass
