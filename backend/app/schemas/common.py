"""
全局通用 RESTful 响应模型与分页查询契约

职责:
    - 统一 RESTful API 返回格式 (code, message, data, trace_id)
    - 统一分页参数与分页响应封装

架构定位:
    数据契约层 (Schemas) / 通用规范

作者:
    System Architect (系统架构组)
"""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """统一 API 响应格式包装存根"""
    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[T] = Field(default=None, description="业务数据载荷")
    trace_id: Optional[str] = Field(default=None, description="全链路追踪标识")


class PaginationParams(BaseModel):
    """通用分页请求参数存根"""
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应载荷存根"""
    items: List[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=10, description="每页记录数")
