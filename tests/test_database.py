# tests/test_database.py
import pytest
import aiosqlite
import os
from database import init_db, get_db


@pytest.fixture
def db_path(tmp_path):
    """创建临时数据库路径"""
    return str(tmp_path / "test.db")


@pytest.mark.asyncio
async def test_init_db_creates_table(db_path):
    """测试初始化数据库创建表"""
    await init_db(db_path)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mysql_metrics'"
        )
        table = await cursor.fetchone()
        assert table is not None


@pytest.mark.asyncio
async def test_get_db_returns_connection(db_path):
    """测试获取数据库连接"""
    await init_db(db_path)

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT 1")
        result = await cursor.fetchone()
        assert result[0] == 1
