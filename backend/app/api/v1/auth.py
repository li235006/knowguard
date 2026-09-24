"""
认证与授权控制器 (Auth Router)

接口清单:
    - POST /api/v1/auth/login: 用户登录并签发 Token
    - POST /api/v1/auth/refresh: 刷新 Access Token
    - POST /api/v1/auth/logout: 退出登录并作废 Token
    - GET  /api/v1/auth/me: 获取当前登录员工上下文信息

架构定位:
    API 控制器层 / 模块一: IAM 中心

作者:
    System Architect (系统架构组)
"""

from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, TokenResponse, UserContext
from app.schemas.common import StandardResponse

router = APIRouter()


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(payload: LoginRequest):
    """用户登录接口存根"""
    pass


@router.post("/refresh", response_model=StandardResponse[TokenResponse])
async def refresh_token():
    """刷新 Token 接口存根"""
    pass


@router.post("/logout", response_model=StandardResponse[bool])
async def logout():
    """退出登录接口存根"""
    pass


@router.get("/me", response_model=StandardResponse[UserContext])
async def get_current_user_profile():
    """获取当前用户身份信息接口存根"""
    pass
