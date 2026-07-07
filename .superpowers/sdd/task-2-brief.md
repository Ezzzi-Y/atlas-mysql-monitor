# Task 2: SQLite 数据库层

## 任务目标
创建 SQLite 数据库管理模块，提供数据库初始化和连接管理功能。

## 文件清单
- 创建：`database.py`
- 创建：`tests/test_database.py`

## 接口产出
- `init_db(db_path=None)`: 初始化数据库，创建表结构
- `get_db(db_path=None)`: 获取数据库连接的上下文管理器
- `DEFAULT_DB_PATH`: 默认数据库路径

## 详细步骤

### Step 1: 编写数据库测试
```python
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
```

### Step 2: 运行测试验证失败
```bash
uv run pytest tests/test_database.py -v
```
预期输出：FAIL（ModuleNotFoundError: No module named 'database'）

### Step 3: 实现 database.py
```python
# database.py
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

# 确保 data 目录存在
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_DB_PATH = DATA_DIR / "monitor.db"


async def init_db(db_path: str = None):
    """初始化数据库，创建表结构"""
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mysql_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
                threads_connected INTEGER,
                threads_running INTEGER,
                uptime INTEGER,
                slow_queries INTEGER,
                com_select INTEGER,
                com_insert INTEGER,
                com_update INTEGER,
                com_delete INTEGER,
                select_qps REAL,
                insert_qps REAL,
                update_qps REAL,
                delete_qps REAL
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON mysql_metrics(timestamp)"
        )
        await db.commit()


@asynccontextmanager
async def get_db(db_path: str = None):
    """获取数据库连接的上下文管理器"""
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)
    
    db = await aiosqlite.connect(db_path)
    try:
        yield db
    finally:
        await db.close()
```

### Step 4: 运行测试验证通过
```bash
uv run pytest tests/test_database.py -v
```
预期输出：2 passed

### Step 5: 提交代码
```bash
git add database.py tests/test_database.py
git commit -m "feat: SQLite 数据库层"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
