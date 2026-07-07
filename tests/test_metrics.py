# tests/test_metrics.py
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from database import init_db
from models.metrics import (
    save_metrics,
    get_latest_metrics,
    get_metrics_history,
    cleanup_old_metrics,
)


@pytest_asyncio.fixture
async def db(tmp_path):
    """创建测试数据库"""
    db_path = str(tmp_path / "test.db")
    await init_db(db_path)
    return db_path


@pytest.mark.asyncio
async def test_save_and_get_latest_metrics(db):
    """测试保存和获取最新指标"""
    metrics = {
        "threads_connected": 10,
        "threads_running": 2,
        "uptime": 3600,
        "slow_queries": 5,
        "com_select": 1000,
        "com_insert": 100,
        "com_update": 50,
        "com_delete": 10,
        "select_qps": 16.67,
        "insert_qps": 1.67,
        "update_qps": 0.83,
        "delete_qps": 0.17,
    }

    await save_metrics(db, metrics)
    latest = await get_latest_metrics(db)

    assert latest is not None
    assert latest["threads_connected"] == 10
    assert latest["select_qps"] == 16.67


@pytest.mark.asyncio
async def test_get_metrics_history(db):
    """测试获取指标历史"""
    # 插入多条记录
    for i in range(5):
        metrics = {
            "threads_connected": 10 + i,
            "threads_running": 2,
            "uptime": 3600 + i * 60,
            "slow_queries": 5,
            "com_select": 1000 + i * 100,
            "com_insert": 100,
            "com_update": 50,
            "com_delete": 10,
            "select_qps": 16.67,
            "insert_qps": 1.67,
            "update_qps": 0.83,
            "delete_qps": 0.17,
        }
        await save_metrics(db, metrics)

    history = await get_metrics_history(db, hours=1)
    assert len(history) == 5


@pytest.mark.asyncio
async def test_cleanup_old_metrics(db):
    """测试清理过期数据"""
    # 插入一条旧数据（手动设置 timestamp）
    metrics = {
        "threads_connected": 10,
        "threads_running": 2,
        "uptime": 3600,
        "slow_queries": 5,
        "com_select": 1000,
        "com_insert": 100,
        "com_update": 50,
        "com_delete": 10,
        "select_qps": 16.67,
        "insert_qps": 1.67,
        "update_qps": 0.83,
        "delete_qps": 0.17,
    }
    await save_metrics(db, metrics)

    # 手动修改 timestamp 为 31 天前
    import aiosqlite
    async with aiosqlite.connect(db) as conn:
        old_time = datetime.now() - timedelta(days=31)
        await conn.execute(
            "UPDATE mysql_metrics SET timestamp = ?",
            (old_time.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        await conn.commit()

    # 清理 30 天前的数据
    deleted = await cleanup_old_metrics(db, retention_days=30)
    assert deleted == 1

    # 验证数据已删除
    latest = await get_latest_metrics(db)
    assert latest is None
