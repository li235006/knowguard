"""
身份认证与 Token 交互数据契约 (Auth Schemas)

职责:
    - 登录请求与响应模型
    - Token 刷新与 Claims 载荷模型
    - 当前登录用户上下文 (UserContext) 模型

架构定位:
    数据契约层 (Schemas) / 模块一: IAM 中心

作者:
    System Architect (系统架构组)
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """用户登录请求入参存根"""
    username: str = Field(..., description="账号/工号")
    password: str = Field(..., description="登录密码")


class TokenResponse(BaseModel):
    """Token 颁发响应载荷存根"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT Token 内部有效载荷存根"""
    sub: str = Field(..., description="用户唯一标识 (userId)")
    username: str
    dept_id: int
    role_ids: List[int]
    permissions: List[str]
    exp: int


class UserContext(BaseModel):
    """请求上下文当前登录用户实体存根"""
    user_id: int
    username: str
    dept_id: int
    role_ids: List[int]
    permissions: List[str]
