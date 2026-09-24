"""
身份认证与 Token 交互数据契约 (Auth Schemas)

职责:
    - 登录请求与响应模型
    - Token 刷新与 Claims 载荷模型
    - 当前登录用户上下文 (UserContext) 模型

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

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """用户登录请求入参"""
    username: str = Field(..., min_length=1, max_length=64, description="账号/工号")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码")


class TokenResponse(BaseModel):
    """Token 颁发响应载荷"""
    access_token: str = Field(..., description="JWT Access Token (120分钟有效)")
    refresh_token: str = Field(..., description="JWT Refresh Token (7天有效)")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="Access Token 过期秒数 (7200秒)")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求入参"""
    refresh_token: str = Field(..., description="用于无感续签的 Refresh Token")


class TokenPayload(BaseModel):
    """JWT Token 内部有效载荷"""
    sub: str = Field(..., description="用户唯一标识 (userId)")
    username: str = Field(..., description="登录账号")
    employee_id: Optional[str] = Field(default=None, description="工号")
    dept_id: Optional[int] = Field(default=None, description="所属部门ID")
    dept_name: Optional[str] = Field(default=None, description="所属部门名称")
    role_code: Optional[str] = Field(default=None, description="主角色编码")
    role_codes: List[str] = Field(default_factory=list, description="绑定角色编码列表")
    role_ids: List[int] = Field(default_factory=list, description="绑定角色ID列表")
    permissions: List[str] = Field(default_factory=list, description="细粒度操作权限编码集合")
    is_superuser: bool = Field(default=False, description="是否系统超级管理员")
    token_type: str = Field(default="access", description="令牌类型: access / refresh")
    exp: int = Field(..., description="过期时间戳 (UTC)")
    iat: Optional[int] = Field(default=None, description="签发时间戳")


class UserContext(BaseModel):
    """请求上下文当前登录用户实体"""
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., description="用户主键ID")
    employee_id: str = Field(..., description="工号")
    username: str = Field(..., description="登录账号")
    real_name: str = Field(..., description="真实姓名")
    dept_id: Optional[int] = Field(default=None, description="归属部门ID")
    dept_name: Optional[str] = Field(default=None, description="归属部门名称")
    role_code: Optional[str] = Field(default=None, description="主角色编码")
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")
    role_codes: List[str] = Field(default_factory=list, description="角色编码列表")
    permissions: List[str] = Field(default_factory=list, description="权限代码列表")
    avatar: Optional[str] = Field(default=None, description="头像地址")
    is_superuser: bool = Field(default=False, description="是否系统超级管理员")


if __name__ == "__main__":
    print("=== [Self-Test] Starting Auth Schemas Self-Test ===")
    req = LoginRequest(username="zhangsan", password="Password123!")
    assert req.username == "zhangsan"

    ctx = UserContext(
        user_id=1,
        employee_id="10086",
        username="zhangsan",
        real_name="张三",
        dept_id=2,
        dept_name="技术研发中心",
        role_ids=[1],
        role_codes=["ROLE_SUPER_ADMIN"],
        permissions=["knowledge:view", "knowledge:import"],
        is_superuser=True
    )
    assert ctx.real_name == "张三"
    assert "knowledge:view" in ctx.permissions
    print("=== [Self-Test] All Auth Schemas tests PASSED successfully! ===")
