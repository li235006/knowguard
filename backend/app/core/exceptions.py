"""
KnowGuard 全局统一业务异常体系定义

职责:
    - 统一定义全系统核心领域业务异常基类与派生子类
    - 支持携带 HTTP 状态码、业务错误码、错误提示与详细上下文字段

架构定位:
    核心底层支撑层 (Core Infrastructure) / 异常控制

作者:
    System Architect (系统架构组)
"""

from typing import Any, Dict, Optional


class KnowGuardException(Exception):
    """KnowGuard 业务异常基类存根"""

    def __init__(
        self,
        code: int = 50000,
        message: str = "Internal Server Error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(KnowGuardException):
    """用户认证失败或 Token 无效/过期异常存根"""
    pass


class PermissionDeniedError(KnowGuardException):
    """用户操作权限不足 (RBAC 拦截) 异常存根"""
    pass


class EntityNotFoundError(KnowGuardException):
    """请求的业务资源实体未找到异常存根"""
    pass


class GuardSecurityViolation(KnowGuardException):
    """4D 数据权限动态拦截与越权访问告警异常存根"""
    pass


class ModelProviderError(KnowGuardException):
    """外部大模型/嵌入向量提供商调用异常存根"""
    pass
