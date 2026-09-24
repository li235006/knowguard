"""
KnowGuard 全局统一业务异常体系定义

职责:
    - 统一定义全系统核心领域业务异常基类与派生子类
    - 支持携带 HTTP 状态码、业务错误码、错误提示与详细上下文字段

架构定位:
    核心底层支撑层 (Core Infrastructure) / 异常控制

作者:
    System Architect (系统架构组) & Backend Team
"""

from typing import Any, Dict, Optional


class KnowGuardException(Exception):
    """KnowGuard 业务异常基类"""

    def __init__(
        self,
        code: int = 50001,
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
    """用户认证失败或 Token 无效/过期异常 (40101)"""

    def __init__(
        self,
        message: str = "认证失败，请重新登录",
        code: int = 40101,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=401,
            details=details,
        )


class PermissionDeniedError(KnowGuardException):
    """用户操作权限不足 (RBAC 拦截) 异常 (40301)"""

    def __init__(
        self,
        message: str = "权限不足，拒绝访问",
        code: int = 40301,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=403,
            details=details,
        )


class EntityNotFoundError(KnowGuardException):
    """请求的业务资源实体未找到异常 (40401)"""

    def __init__(
        self,
        message: str = "请求的资源不存在",
        code: int = 40401,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=404,
            details=details,
        )


class BusinessLogicError(KnowGuardException):
    """业务逻辑或参数校验阻断异常 (40001)"""

    def __init__(
        self,
        message: str = "业务校验未通过",
        code: int = 40001,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=400,
            details=details,
        )


class GuardSecurityViolation(KnowGuardException):
    """4D 数据权限动态拦截与越权访问告警异常 (40301)"""

    def __init__(
        self,
        message: str = "4D数据安全策略拦截",
        code: int = 40301,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=403,
            details=details,
        )


class ModelProviderError(KnowGuardException):
    """外部大模型/嵌入向量提供商调用异常 (50002)"""

    def __init__(
        self,
        message: str = "大模型服务调用异常",
        code: int = 50002,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=500,
            details=details,
        )
