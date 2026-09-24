"""
组织员工、部门树及角色权限数据契约 (User Schemas)

职责:
    - 部门增删改查及 8 级树形结构展示模型
    - 员工账号 CRUD、状态维护模型
    - 角色管理及菜单/路由/按钮三级 RBAC 授权树模型

架构定位:
    数据契约层 (Schemas) / 模块一: IAM 中心

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==================== 部门相关 Schema ====================

class DepartmentBase(BaseModel):
    """部门基础模型"""
    name: str = Field(..., min_length=1, max_length=64, description="部门名称")
    code: str = Field(..., min_length=1, max_length=64, description="部门编码")
    parent_id: Optional[int] = Field(default=None, description="父部门ID (根部门为 None)")
    sort_order: int = Field(default=0, description="展示排序序号")
    leader_name: Optional[str] = Field(default=None, max_length=64, description="负责人姓名")
    phone: Optional[str] = Field(default=None, max_length=32, description="联系电话")
    email: Optional[str] = Field(default=None, max_length=128, description="联系邮箱")
    status: bool = Field(default=True, description="部门状态 (True正常, False停用)")


class DepartmentCreate(DepartmentBase):
    """创建部门请求入参"""
    pass


class DepartmentUpdate(BaseModel):
    """更新部门请求入参"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=64, description="部门名称")
    code: Optional[str] = Field(default=None, min_length=1, max_length=64, description="部门编码")
    parent_id: Optional[int] = Field(default=None, description="父部门ID")
    sort_order: Optional[int] = Field(default=None, description="展示排序序号")
    leader_name: Optional[str] = Field(default=None, max_length=64, description="负责人姓名")
    phone: Optional[str] = Field(default=None, max_length=32, description="联系电话")
    email: Optional[str] = Field(default=None, max_length=128, description="联系邮箱")
    status: Optional[bool] = Field(default=None, description="部门状态")


class DepartmentResponse(DepartmentBase):
    """部门单节点响应载荷"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="部门主键ID")
    materialized_path: str = Field(..., description="物化路径，如 /1/3/")
    level: int = Field(..., ge=1, le=8, description="部门层级 (1-8 级)")
    user_count: int = Field(default=0, description="部门成员人数")
    member_count: Optional[int] = Field(default=0, description="部门成员人数 (前端别名)")
    direct_user_count: Optional[int] = Field(default=0, description="部门直属成员人数")
    direct_member_count: Optional[int] = Field(default=0, description="部门直属成员人数")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class DepartmentTreeResponse(DepartmentResponse):
    """部门树形递归节点响应载荷"""
    children: List["DepartmentTreeResponse"] = Field(default_factory=list, description="子部门列表")


# ==================== 角色与权限相关 Schema ====================

class PermissionTreeNode(BaseModel):
    """RBAC 三级权限树节点 (菜单 ➔ 路由 ➔ 按钮)"""
    id: str = Field(..., description="节点唯一键 (code 或 id)")
    label: str = Field(..., description="显示名称")
    code: str = Field(..., description="权限标识码")
    type: str = Field(..., description="节点类型: menu/route/button")
    resource_path: Optional[str] = Field(default=None, description="页面路由或API资源")
    children: List["PermissionTreeNode"] = Field(default_factory=list, description="下级权限节点")


class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., min_length=1, max_length=64, description="角色名称")
    code: str = Field(..., min_length=1, max_length=64, description="角色编码")
    description: Optional[str] = Field(default=None, max_length=255, description="角色描述")
    status: bool = Field(default=True, description="启停用状态")


class RoleCreate(RoleBase):
    """创建角色请求入参"""
    permission_codes: List[str] = Field(default_factory=list, description="分配的权限代码列表")


class RoleUpdate(BaseModel):
    """更新角色请求入参"""
    name: Optional[str] = Field(default=None, max_length=64, description="角色名称")
    code: Optional[str] = Field(default=None, max_length=64, description="角色编码")
    description: Optional[str] = Field(default=None, max_length=255, description="角色描述")
    status: Optional[bool] = Field(default=None, description="启停用状态")
    permission_codes: Optional[List[str]] = Field(default=None, description="分配的权限代码列表")
    permissions: Optional[List[str]] = Field(default=None, description="分配的权限代码列表 (前端兼容字段)")


class RolePermissionUpdate(BaseModel):
    """分配角色权限入参"""
    permission_codes: Optional[List[str]] = Field(default=None, description="分配的权限编码全集")
    permissions: Optional[List[str]] = Field(default=None, description="分配的权限编码全集 (前端兼容字段)")

    def get_codes(self) -> List[str]:
        return self.permission_codes if self.permission_codes is not None else (self.permissions or [])


class RoleResponse(RoleBase):
    """角色详情响应载荷"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="角色ID")
    is_system: bool = Field(default=False, description="是否系统内置角色")
    permission_codes: List[str] = Field(default_factory=list, description="权限代码列表")
    permissions: List[str] = Field(default_factory=list, description="权限代码列表 (前端兼容别名)")
    user_count: int = Field(default=0, description="绑定该角色的员工数")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

    @model_validator(mode="after")
    def sync_permissions(self) -> "RoleResponse":
        if self.permission_codes and not self.permissions:
            self.permissions = list(self.permission_codes)
        elif self.permissions and not self.permission_codes:
            self.permission_codes = list(self.permissions)
        return self


# ==================== 员工用户相关 Schema ====================

class UserBase(BaseModel):
    """员工基础模型"""
    employee_id: str = Field(..., min_length=1, max_length=32, description="工号，如 10086")
    username: str = Field(..., min_length=1, max_length=64, description="登录账号")
    real_name: str = Field(..., min_length=1, max_length=64, description="员工姓名")
    email: Optional[str] = Field(default=None, max_length=128, description="工作邮箱")
    phone: Optional[str] = Field(default=None, max_length=32, description="联系电话")
    avatar: Optional[str] = Field(default=None, max_length=255, description="头像URL")
    department_id: Optional[int] = Field(default=None, description="所属部门ID")
    is_active: bool = Field(default=True, description="账号启停用状态")
    is_superuser: bool = Field(default=False, description="是否超级管理员")


class UserCreate(UserBase):
    """创建员工请求入参"""
    password: str = Field(..., min_length=6, max_length=128, description="初始登录密码")
    role_ids: List[int] = Field(default_factory=list, description="关联角色ID列表")
    dept_id: Optional[int] = Field(default=None, description="所属部门ID (前端兼容字段)")


class UserUpdate(BaseModel):
    """修改员工信息请求入参"""
    real_name: Optional[str] = Field(default=None, min_length=1, max_length=64, description="真实姓名")
    email: Optional[str] = Field(default=None, max_length=128, description="工作邮箱")
    phone: Optional[str] = Field(default=None, max_length=32, description="联系电话")
    avatar: Optional[str] = Field(default=None, max_length=255, description="头像URL")
    department_id: Optional[int] = Field(default=None, description="所属部门ID")
    dept_id: Optional[int] = Field(default=None, description="所属部门ID (前端兼容字段)")
    role_ids: Optional[List[int]] = Field(default=None, description="关联角色ID列表")
    password: Optional[str] = Field(default=None, min_length=6, max_length=128, description="重置密码")
    is_active: Optional[bool] = Field(default=None, description="账号状态")


class UserPasswordReset(BaseModel):
    """重置密码请求入参"""
    new_password: Optional[str] = Field(default="Password123!", min_length=6, max_length=128, description="新密码")
    password: Optional[str] = Field(default=None, description="新密码 (前端兼容字段)")


class UserStatusUpdate(BaseModel):
    """启停用员工账号入参"""
    is_active: Optional[bool] = Field(default=None, description="账号状态 (True启用, False停用)")
    status: Optional[Any] = Field(default=None, description="账号状态 (兼容字段)")

    def get_is_active(self) -> bool:
        if self.is_active is not None:
            return bool(self.is_active)
        if self.status is not None:
            if isinstance(self.status, bool):
                return self.status
            if isinstance(self.status, (int, float)):
                return bool(self.status)
            if isinstance(self.status, str):
                return self.status.lower() in ("true", "1", "active", "enable", "enabled")
        return True


class UserResponse(UserBase):
    """员工详情响应载荷"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    department_name: Optional[str] = Field(default=None, description="所属部门名称")
    roles: List[RoleResponse] = Field(default_factory=list, description="所属角色列表")
    dept_id: Optional[int] = Field(default=None, description="所属部门ID (前端别名)")
    dept_name: Optional[str] = Field(default=None, description="所属部门名称 (前端别名)")
    role_ids: List[int] = Field(default_factory=list, description="关联角色ID列表")
    role_names: List[str] = Field(default_factory=list, description="关联角色名称列表")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

    @model_validator(mode="after")
    def sync_user_fields(self) -> "UserResponse":
        if self.dept_id is None and self.department_id is not None:
            self.dept_id = self.department_id
        elif self.department_id is None and self.dept_id is not None:
            self.department_id = self.dept_id
        if self.dept_name is None and self.department_name is not None:
            self.dept_name = self.department_name
        elif self.department_name is None and self.dept_name is not None:
            self.department_name = self.dept_name
        if self.roles:
            if not self.role_ids:
                self.role_ids = [r.id for r in self.roles]
            if not self.role_names:
                self.role_names = [r.name for r in self.roles]
        return self



if __name__ == "__main__":
    print("=== [Self-Test] Starting User Schemas Self-Test ===")
    dept_create = DepartmentCreate(
        name="技术研发中心",
        code="TECH_CENTER",
        parent_id=1,
        leader_name="李四"
    )
    assert dept_create.name == "技术研发中心"

    user_create = UserCreate(
        employee_id="10086",
        username="zhangsan",
        real_name="张三",
        password="Password123!",
        department_id=1,
        role_ids=[1, 2]
    )
    assert user_create.employee_id == "10086"
    assert len(user_create.role_ids) == 2

    tree_node = DepartmentTreeResponse(
        id=1,
        name="集团总部",
        code="CORP",
        parent_id=None,
        materialized_path="/1/",
        level=1,
        sort_order=0,
        status=True,
        children=[]
    )
    assert tree_node.level == 1
    print("=== [Self-Test] All User Schemas tests PASSED successfully! ===")
