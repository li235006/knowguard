"""
四维细粒度数据权限与鉴权决策控制器 (Guard Router)

接口清单:
    - GET  /api/v1/guard/units/{unit_id}/policy: 获取知识单元 4D 权限策略 (Leader 标准路由)
    - PUT  /api/v1/guard/units/{unit_id}/policy: 更新知识单元 4D 权限策略 (Leader 标准路由)
    - GET  /api/v1/guard/policies/{unit_id}: 兼容前端路径获取 4D 策略
    - PUT  /api/v1/guard/policies/{unit_id}: 兼容前端路径更新 4D 策略
    - POST /api/v1/guard/check-access: 批量计算知识单元放行与受限集合
    - POST /api/v1/guard/check-chunks: 批量计算切片级放行与受限集合 (filter_allowed_chunks)

架构定位:
    API 控制器层 / 模块三: 4D 权限与安全护栏

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import Optional
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import EntityNotFoundError
from app.middlewares.auth_middleware import get_current_user
from app.models.knowledge import KnowledgeUnit
from app.schemas.auth import UserContext
from app.schemas.common import StandardResponse
from app.schemas.guard import (
    AccessCheckRequest,
    AccessCheckResult,
    ChunkAccessCheckRequest,
    ChunkAccessCheckResult,
    PermissionPolicyConfig,
    PermissionPolicyResponse,
)
from app.services.guard_service import GuardService

router = APIRouter()


async def get_optional_user(
    request: Request,
) -> Optional[UserContext]:
    """解析可选用户上下文（无 Token 时返回 None）"""
    try:
        if hasattr(request.state, "user") and request.state.user:
            payload = request.state.user
            return UserContext(
                user_id=int(payload.get("user_id", payload.get("sub", 0))),
                employee_id=payload.get("employee_id", ""),
                username=payload.get("username", ""),
                real_name=payload.get("real_name", payload.get("username", "")),
                dept_id=payload.get("dept_id"),
                dept_name=payload.get("dept_name"),
                role_code=payload.get("role_code"),
                role_ids=payload.get("role_ids", []),
                role_codes=payload.get("role_codes", []),
                permissions=payload.get("permissions", []),
                is_superuser=payload.get("is_superuser", False),
            )
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from app.core.security import decode_token
            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            return UserContext(
                user_id=int(payload.get("user_id", payload.get("sub", 0))),
                employee_id=payload.get("employee_id", ""),
                username=payload.get("username", ""),
                real_name=payload.get("real_name", payload.get("username", "")),
                dept_id=payload.get("dept_id"),
                dept_name=payload.get("dept_name"),
                role_code=payload.get("role_code"),
                role_ids=payload.get("role_ids", []),
                role_codes=payload.get("role_codes", []),
                permissions=payload.get("permissions", []),
                is_superuser=payload.get("is_superuser", False),
            )
    except Exception:
        pass
    return None


@router.get("/units/{unit_id}/policy", response_model=StandardResponse[PermissionPolicyResponse])
@router.get("/policies/{unit_id}", response_model=StandardResponse[PermissionPolicyResponse])
async def get_unit_policy(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定知识单元的 4D 权限策略配置
    若尚未显式配置，返回系统默认非公开 (Private-by-default) 策略
    """
    # 确认知识单元存在
    doc_res = await db.execute(select(KnowledgeUnit).where(KnowledgeUnit.id == unit_id))
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise EntityNotFoundError(message=f"知识单元 ID={unit_id} 不存在", code=40401)

    service = GuardService(db=db)
    policy = await service.get_unit_policy(unit_id)
    if policy is None:
        # 返回默认非公开策略
        default_data = PermissionPolicyResponse(
            unit_id=unit_id,
            is_public=False,
            is_global=False,
            department_ids=[],
            role_ids=[],
            user_ids=[],
            updated_at=doc.created_at,
        )
        return StandardResponse(
            code=200,
            message="获取默认4D权限策略成功",
            data=default_data,
        )

    res_data = PermissionPolicyResponse.model_validate(policy)
    return StandardResponse(
        code=200,
        message="获取4D权限策略成功",
        data=res_data,
    )


@router.put("/units/{unit_id}/policy", response_model=StandardResponse[PermissionPolicyResponse])
@router.put("/policies/{unit_id}", response_model=StandardResponse[PermissionPolicyResponse])
async def update_unit_policy(
    unit_id: int,
    payload: PermissionPolicyConfig,
    db: AsyncSession = Depends(get_db),
):
    """
    配置或更新知识单元的四维数据权限 (全局/部门/角色/个人)
    """
    service = GuardService(db=db)
    updated_policy = await service.update_unit_policy(unit_id=unit_id, policy_config=payload)
    res_data = PermissionPolicyResponse.model_validate(updated_policy)
    return StandardResponse(
        code=200,
        message="4D权限策略更新成功",
        data=res_data,
    )


@router.post("/check-access", response_model=StandardResponse[AccessCheckResult])
async def check_access(
    payload: AccessCheckRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    知识单元级访问鉴权裁决接口
    根据当前用户上下文 UserContext 与 candidate_unit_ids，执行 OR 充分条件裁决，
    返回放行集合 (allowed_unit_ids) 与拦截集合 (restricted_unit_ids)
    """
    current_user = await get_optional_user(request)
    if not current_user:
        # 匿名用户仅放行公开文档
        current_user = UserContext(
            user_id=0,
            employee_id="anonymous",
            username="anonymous",
            real_name="匿名访客",
            is_superuser=False,
        )

    service = GuardService(db=db)
    allowed, restricted = await service.evaluate_access(current_user, payload.candidate_unit_ids)
    return StandardResponse(
        code=200,
        message="鉴权计算完成",
        data=AccessCheckResult(
            allowed_unit_ids=allowed,
            restricted_unit_ids=restricted,
        ),
    )


@router.post("/check-chunks", response_model=StandardResponse[ChunkAccessCheckResult])
async def check_chunks_access(
    payload: ChunkAccessCheckRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    切片级别访问鉴权过滤接口 (调用 GuardService.filter_allowed_chunks)
    """
    current_user = await get_optional_user(request)
    if not current_user:
        current_user = UserContext(
            user_id=0,
            employee_id="anonymous",
            username="anonymous",
            real_name="匿名访客",
            is_superuser=False,
        )

    service = GuardService(db=db)
    allowed_c, restricted_c = await service.filter_allowed_chunks(current_user, payload.candidate_chunk_ids)
    return StandardResponse(
        code=200,
        message="切片鉴权过滤完成",
        data=ChunkAccessCheckResult(
            allowed_chunk_ids=allowed_c,
            restricted_chunk_ids=restricted_c,
        ),
    )


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base
    from app.core.security import create_access_token
    from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
    from main import create_app

    print("=== [Self-Test] Starting Guard Router Self-Test ===")

    async def _test_guard_router():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _override_get_db():
            async with session_factory() as session:
                yield session

        test_app = create_app()
        test_app.dependency_overrides[get_db] = _override_get_db

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 初始化测试知识单元和切片
            async with session_factory() as session:
                u1 = KnowledgeUnit(title="公司章程.pdf", file_type="pdf", status="INDEXED")
                u2 = KnowledgeUnit(title="薪酬矩阵.pdf", file_type="pdf", status="INDEXED")
                session.add_all([u1, u2])
                await session.commit()
                await session.refresh(u1)
                await session.refresh(u2)

                c1 = KnowledgeChunk(document_id=u1.id, chunk_index=0, content="章程切片", status="indexed")
                c2 = KnowledgeChunk(document_id=u2.id, chunk_index=0, content="薪酬切片", status="indexed")
                session.add_all([c1, c2])
                await session.commit()
                await session.refresh(c1)
                await session.refresh(c2)
                u1_id, u2_id, c1_id, c2_id = u1.id, u2.id, c1.id, c2.id

            # 2. 测试 GET 默认策略 (GET /api/v1/guard/units/{unit_id}/policy)
            get_res = await client.get(f"/api/v1/guard/units/{u1_id}/policy")
            assert get_res.status_code == 200
            pol_data = get_res.json()["data"]
            assert pol_data["unit_id"] == u1_id
            assert pol_data["is_public"] is False
            assert pol_data["is_global"] is False
            print(f"[Self-Test] GET /guard/units/{u1_id}/policy returned default private policy")

            # 3. 测试 PUT 策略配置 (PUT /api/v1/guard/units/{unit_id}/policy)
            put_payload = {
                "is_public": False,
                "is_global": False,
                "department_ids": [2],
                "role_ids": [20],
                "user_ids": [101]
            }
            put_res = await client.put(f"/api/v1/guard/units/{u1_id}/policy", json=put_payload)
            assert put_res.status_code == 200
            put_data = put_res.json()["data"]
            assert put_data["department_ids"] == [2]
            assert put_data["role_ids"] == [20]
            print(f"[Self-Test] PUT /guard/units/{u1_id}/policy updated successfully")

            # 4. 测试前端兼容路径 (GET & PUT /api/v1/guard/policies/{id})
            alias_get = await client.get(f"/api/v1/guard/policies/{u1_id}")
            assert alias_get.status_code == 200
            assert alias_get.json()["data"]["role_ids"] == [20]

            # 将 u2 设置为公开
            await client.put(f"/api/v1/guard/policies/{u2_id}", json={"is_global": True})

            # 5. 模拟普通用户 Token 进行 check-access (dept_id=2 -> 命中 u1，u2 是公开 -> 命中 u2)
            user_token = create_access_token({
                "sub": "101",
                "user_id": 101,
                "employee_id": "10101",
                "username": "rd_zhang",
                "dept_id": 2,
                "role_ids": [999],
                "is_superuser": False,
            })

            access_res = await client.post(
                "/api/v1/guard/check-access",
                json={"candidate_unit_ids": [u1_id, u2_id]},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert access_res.status_code == 200
            access_data = access_res.json()["data"]
            assert set(access_data["allowed_unit_ids"]) == {u1_id, u2_id}
            assert len(access_data["restricted_unit_ids"]) == 0
            print(f"[Self-Test] POST /guard/check-access verified: allowed={access_data['allowed_unit_ids']}")

            # 6. 测试切片级鉴权过滤 (POST /api/v1/guard/check-chunks)
            chunks_res = await client.post(
                "/api/v1/guard/check-chunks",
                json={"candidate_chunk_ids": [c1_id, c2_id, 99999]},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert chunks_res.status_code == 200
            c_data = chunks_res.json()["data"]
            assert set(c_data["allowed_chunk_ids"]) == {c1_id, c2_id}
            assert 99999 in c_data["restricted_chunk_ids"]
            print(f"[Self-Test] POST /guard/check-chunks verified: allowed={c_data['allowed_chunk_ids']}")

        test_app.dependency_overrides.clear()
        await test_engine.dispose()
        print("=== [Self-Test] All Guard Router tests PASSED successfully! ===")

    asyncio.run(_test_guard_router())
