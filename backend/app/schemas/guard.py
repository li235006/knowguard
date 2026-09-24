"""
4D-RBAC 权限策略与安全护栏数据契约 (Guard Schemas)

职责:
    - 四维权限配置请求与详情响应模型 (全局公开/部门树/角色/个人)
    - 内部鉴权调用契约 (UserContext + candidate_unit_ids / candidate_chunk_ids -> allowed / restricted)
    - 保证 is_public 与 is_global 契约别名互通

架构定位:
    数据契约层 (Schemas) / 模块三: 4D 权限与安全护栏

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PermissionPolicyConfig(BaseModel):
    """四维权限配置请求模型 (支持 is_public 与 is_global 智能双向对齐)"""
    is_public: bool = Field(default=False, description="是否全员公开")
    is_global: Optional[bool] = Field(None, description="全员公开兼容别名 (前端等效于 is_public)")
    department_ids: List[int] = Field(default_factory=list, description="授权部门 ID 列表")
    role_ids: List[int] = Field(default_factory=list, description="授权角色 ID 列表")
    user_ids: List[int] = Field(default_factory=list, description="授权员工用户 ID 列表")

    @model_validator(mode="before")
    @classmethod
    def sync_public_and_global(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 若传入 is_global 但未提供 is_public，同步至 is_public
            if "is_global" in data and ("is_public" not in data or data["is_public"] is None):
                data["is_public"] = bool(data["is_global"])
            elif "is_public" in data and ("is_global" not in data or data["is_global"] is None):
                data["is_global"] = bool(data["is_public"])
        return data


class PermissionPolicyResponse(BaseModel):
    """四维权限配置详情响应模型"""
    model_config = ConfigDict(from_attributes=True)

    unit_id: int = Field(..., description="关联知识单元 ID")
    is_public: bool = Field(default=False, description="是否全员公开")
    is_global: bool = Field(default=False, description="全员公开兼容别名")
    department_ids: List[int] = Field(default_factory=list, description="授权部门 ID 列表")
    role_ids: List[int] = Field(default_factory=list, description="授权角色 ID 列表")
    user_ids: List[int] = Field(default_factory=list, description="授权员工用户 ID 列表")
    updated_at: Optional[Union[datetime, str]] = Field(None, description="策略更新时间")

    @model_validator(mode="before")
    @classmethod
    def populate_response_fields(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            is_pub = getattr(data, "is_public", False)
            up_at = getattr(data, "updated_at", None)
            return {
                "unit_id": getattr(data, "unit_id", 0),
                "is_public": is_pub,
                "is_global": is_pub,
                "department_ids": getattr(data, "department_ids", []) or [],
                "role_ids": getattr(data, "role_ids", []) or [],
                "user_ids": getattr(data, "user_ids", []) or [],
                "updated_at": up_at.isoformat() if hasattr(up_at, "isoformat") else str(up_at) if up_at else None,
            }
        elif isinstance(data, dict):
            is_pub = data.get("is_public", data.get("is_global", False))
            data["is_public"] = is_pub
            data["is_global"] = is_pub
        return data


class AccessCheckRequest(BaseModel):
    """知识单元级别动态鉴权请求模型"""
    candidate_unit_ids: List[int] = Field(..., description="待校验权限的知识单元 ID 列表")


class AccessCheckResult(BaseModel):
    """知识单元级别动态鉴权计算结果"""
    allowed_unit_ids: List[int] = Field(default_factory=list, description="放行的知识单元 ID 列表")
    restricted_unit_ids: List[int] = Field(default_factory=list, description="拦截受限的知识单元 ID 列表")


class ChunkAccessCheckRequest(BaseModel):
    """切片级别动态鉴权请求模型"""
    candidate_chunk_ids: List[int] = Field(..., description="待校验权限的切片 ID 列表")


class ChunkAccessCheckResult(BaseModel):
    """切片级别动态鉴权计算结果"""
    allowed_chunk_ids: List[int] = Field(default_factory=list, description="放行的切片 ID 列表")
    restricted_chunk_ids: List[int] = Field(default_factory=list, description="拦截受限的切片 ID 列表")


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    print("=== [Self-Test] Starting Guard Schemas Self-Test ===")

    # 1. 验证 is_global 自动同步至 is_public
    cfg1 = PermissionPolicyConfig.model_validate({"is_global": True, "department_ids": [1]})
    assert cfg1.is_public is True
    assert cfg1.is_global is True
    print(f"[Self-Test] PermissionPolicyConfig synced is_global -> is_public: {cfg1.is_public}")

    # 2. 验证 is_public 自动同步至 is_global
    cfg2 = PermissionPolicyConfig.model_validate({"is_public": False, "role_ids": [10]})
    assert cfg2.is_public is False
    assert cfg2.is_global is False
    print(f"[Self-Test] PermissionPolicyConfig synced is_public -> is_global: {cfg2.is_global}")

    # 3. 验证 PermissionPolicyResponse
    res = PermissionPolicyResponse.model_validate({
        "unit_id": 99,
        "is_public": True,
        "department_ids": [1, 2],
        "role_ids": [10],
        "user_ids": [10086],
        "updated_at": "2026-09-24T12:00:00"
    })
    assert res.unit_id == 99
    assert res.is_global is True
    assert len(res.department_ids) == 2
    print(f"[Self-Test] PermissionPolicyResponse verified: unit_id={res.unit_id}")

    # 4. 验证 AccessCheckResult
    chk_res = AccessCheckResult(allowed_unit_ids=[1, 2], restricted_unit_ids=[3, 4])
    assert len(chk_res.allowed_unit_ids) == 2
    assert len(chk_res.restricted_unit_ids) == 2
    print("[Self-Test] AccessCheckResult validated successfully")

    print("=== [Self-Test] All Guard Schemas tests PASSED successfully! ===")
