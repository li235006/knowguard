"""
KnowGuard 系统数据播种脚本 (Seed Script)

职责:
    - 预置基础部门: 管理层、研发部、财务部
    - 预置 6 大内置角色与三级 RBAC 授权树
    - 预置三账号:
        1. 张三 (工号: 10086 / 部门: 研发部 / 角色: 普通员工 / 密码: 123456)
        2. 李四 (工号: 10087 / 部门: 财务部 / 角色: 部门经理 / 密码: 123456)
        3. 王五 (工号: 10088 / 部门: 管理层 / 角色: 系统管理员 / 密码: 123456 / 超管: 是)
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.core.config import settings
from app.core.database import Base, engine
from app.services.iam_service import IAMService


async def seed(db_engine=None):
    """执行 Seed 播种任务"""
    target_engine = db_engine or engine
    print(f"=== [KnowGuard Seed] Initializing Database & Seed Data ===")
    
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=target_engine, expire_on_commit=False)
    async with session_maker() as session:
        service = IAMService(session)
        result = await service.seed_data()
        print(f"[KnowGuard Seed] Departments initialized: {result['departments']}")
        print(f"[KnowGuard Seed] Roles initialized: {result['roles']}")
        for acc in result["accounts"]:
            print(f"[KnowGuard Seed] User seeded: {acc['real_name']} ({acc['employee_id']}) -> Dept ID: {acc['dept_id']}, Role: {acc['role_code']}")

    print("=== [KnowGuard Seed] Database Seed COMPLETED successfully! ===")
    return result


async def main():
    try:
        await seed(engine)
        await engine.dispose()
    except Exception as e:
        print(f"[KnowGuard Seed] Remote MySQL database unavailable ({e}), using local SQLite test environment...")
        local_engine = create_async_engine("sqlite+aiosqlite:///knowguard_seed.db", echo=False)
        await seed(local_engine)
        await local_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

