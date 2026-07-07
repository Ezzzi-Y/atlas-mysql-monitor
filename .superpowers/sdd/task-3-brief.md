# Task 3: 指标数据模型

## 任务目标
创建指标数据模型模块，提供指标的 CRUD 操作功能。

## 文件清单
- 创建：`models/__init__.py`
- 创建：`models/metrics.py`
- 创建：`tests/test_metrics.py`

## 接口产出
- `save_metrics(db_path, metrics)`: 保存一条指标记录
- `get_latest_metrics(db_path)`: 获取最新一条指标
- `get_metrics_history(db_path, hours=24)`: 获取最近 N 小时的指标历史
- `cleanup_old_metrics(db_path, retention_days=30)`: 清理超过保留天数的旧数据

## 详细步骤

### Step 1: 编写指标模型测试
```python
# tests/test_metrics.py
import pytest
import asyncio
from datetime import datetime, timedelta
from database import init_db
from models.metrics import (
    save_metrics,
    get_latest_metrics,
    get_metrics_history,
    cleanup_old_metrics,
)


@pytest.fixture
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
```

### Step 2: 运行测试验证失败
```bash
uv run pytest tests/test_metrics.py -v
```
预期输出：FAIL（ModuleNotFoundError）

### Step 3: 实现 models/metrics.py
```python
# models/metrics.py
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


async def save_metrics(db_path: str, metrics: Dict[str, Any]) -> None:
    """保存一条指标记录"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO mysql_metrics (
                threads_connected, threads_running, uptime, slow_queries,
                com_select, com_insert, com_update, com_delete,
                select_qps, insert_qps, update_qps, delete_qps
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics["threads_connected"],
            metrics["threads_running"],
            metrics["uptime"],
            metrics["slow_queries"],
            metrics["com_select"],
            metrics["com_insert"],
            metrics["com_update"],
            metrics["com_delete"],
            metrics["select_qps"],
            metrics["insert_qps"],
            metrics["update_qps"],
            metrics["delete_qps"],
        ))
        await db.commit()


async def get_latest_metrics(db_path: str) -> Optional[Dict[str, Any]]:
    """获取最新一条指标"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM mysql_metrics ORDER BY id DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_metrics_history(db_path: str, hours: int = 24) -> List[Dict[str, Any]]:
    """获取最近 N 小时的指标历史"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        since = datetime.now() - timedelta(hours=hours)
        cursor = await db.execute(
            "SELECT * FROM mysql_metrics WHERE timestamp >= ? ORDER BY timestamp",
            (since.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def cleanup_old_metrics(db_path: str, retention_days: int = 30) -> int:
    """清理超过保留天数的旧数据，返回删除的行数"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        cutoff = datetime.now() - timedelta(days=retention_days)
        cursor = await db.execute(
            "DELETE FROM mysql_metrics WHERE timestamp < ?",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        await db.commit()
        return cursor.rowcount
```

### Step 4: 运行测试验证通过
```bash
uv run pytest tests/test_metrics.py -v
```
预期输出：3 passed

### Step 5: 提交代码
```bash
git add models/ tests/test_metrics.py
git commit -m "feat: 指标数据模型"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
