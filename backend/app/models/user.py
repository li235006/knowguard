"""
组织架构与身份鉴权实体模型 (User, Department, Role, RolePermission, UserRole)

职责:
    - 部门树形层级模型 (Department): 8 级部门树、物化路径编码、父子关联
    - 用户账号模型 (User): 工号、姓名、部门外键、密码散列密文、启停用状态
    - 角色定义模型 (Role): 系统角色定义 (5 大预置角色及自定义角色)
    - 角色权限映射模型 (RolePermission): 菜单级、路由级与按钮操作级 RBAC 映射表
    - 用户角色多对多映射模型 (UserRole)

架构定位:
    持久化数据模型层 (Data Models) / 模块一: IAM 中心

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Department(BaseModel):
    """部门组织实体"""
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="部门名称")
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True, comment="部门唯一标识编码")
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True, index=True, comment="父部门ID")
    materialized_path: Mapped[str] = mapped_column(String(255), default="/", nullable=False, index=True, comment="物化路径，如 /1/3/")
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="部门层级 (1-8 级)")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序序号")
    leader_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="部门负责人")
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="联系电话")
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="部门邮箱")
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="启停用状态")

    # 父子关联与反向关联
    parent: Mapped[Optional["Department"]] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children"
    )
    children: Mapped[List["Department"]] = relationship(
        "Department",
        back_populates="parent",
        cascade="all"
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="department"
    )


class Role(BaseModel):
    """角色定义实体"""
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色名称")
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True, comment="角色编码")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="角色描述")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否系统内置角色")
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="启停用状态")

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles"
    )
    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class RolePermission(BaseModel):
    """角色与权限映射实体 (三级 RBAC: 菜单、路由、按钮)"""
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="权限唯一标识")
    permission_type: Mapped[str] = mapped_column(String(32), default="button", nullable=False, comment="权限分类: menu/route/button")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="权限名称")
    resource_path: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="前端路由或后端API路径")

    role: Mapped["Role"] = relationship("Role", back_populates="permissions")


class User(BaseModel):
    """用户员工实体"""
    __tablename__ = "users"

    employee_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True, comment="工号，如 10086")
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="登录用户名")
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="员工真实姓名")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment="Bcrypt 工作因子 12 密文")
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="企业邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="联系手机")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="头像URL")
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True, index=True, comment="所属部门ID")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="账号状态: 1正常 0禁用")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否超级管理员")

    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="users", lazy="selectin")
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )


class UserRole(BaseModel):
    """用户与角色多对多关联实体"""
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)


if __name__ == "__main__":
    print("=== [Self-Test] Starting User Models Self-Test ===")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.database import Base

    # 使用 SQLite 内存引擎独立脱机测试 ORM 表结构与关联映射
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        # 1. 验证部门模型与层级字段
        root_dept = Department(
            name="集团总部",
            code="CORP_HQ",
            parent_id=None,
            materialized_path="/1/",
            level=1,
            leader_name="张总"
        )
        session.add(root_dept)
        session.flush()

        sub_dept = Department(
            name="技术研发中心",
            code="TECH_CENTER",
            parent_id=root_dept.id,
            materialized_path=f"/1/{root_dept.id}/",
            level=2,
            leader_name="李主管"
        )
        session.add(sub_dept)
        session.flush()

        # 2. 验证角色与三级权限模型
        admin_role = Role(
            name="超级管理员",
            code="ROLE_SUPER_ADMIN",
            is_system=True,
            description="拥有系统全量控制权限"
        )
        perm = RolePermission(
            role=admin_role,
            permission_code="knowledge:view",
            permission_type="route",
            name="资产检索与台账列表",
            resource_path="/admin/knowledge"
        )
        session.add(admin_role)
        session.add(perm)
        session.flush()

        # 3. 验证用户模型及外键与多对多关联
        user = User(
            employee_id="10086",
            username="zhangsan",
            real_name="张三",
            hashed_password="$2b$12$fakehashedpasswordfortestpurposesonly12345",
            department_id=sub_dept.id,
            is_active=True
        )
        user.roles.append(admin_role)
        session.add(user)
        session.commit()

        # 4. 断言验证
        queried_user = session.query(User).filter_by(username="zhangsan").first()
        assert queried_user is not None, "用户必须正确持久化"
        assert queried_user.employee_id == "10086"
        assert queried_user.department.name == "技术研发中心"
        assert len(queried_user.roles) == 1
        assert queried_user.roles[0].code == "ROLE_SUPER_ADMIN"
        assert len(queried_user.roles[0].permissions) == 1
        assert queried_user.roles[0].permissions[0].permission_code == "knowledge:view"

        print(f"[Self-Test] Department materialized_path: {sub_dept.materialized_path}, level: {sub_dept.level}")
        print(f"[Self-Test] User {queried_user.real_name} linked to Dept: {queried_user.department.name}, Role: {queried_user.roles[0].name}")

    print("=== [Self-Test] All User Models tests PASSED successfully! ===")
