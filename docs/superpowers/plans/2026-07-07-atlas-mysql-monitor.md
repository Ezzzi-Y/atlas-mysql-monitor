# Atlas MySQL Monitor 实施计划

> **给智能体工作者：** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 来逐任务实施本计划。步骤使用 checkbox（`- [ ]`）语法进行跟踪。

**目标：** 从零构建一个基于 FastAPI 的 MySQL 监控工具，支持定时采集基础指标、SQLite 存储、SSR 仪表盘展示。

**架构：** 模块化结构，按职责划分：配置管理 → 数据库层 → 采集器 → 路由 → 前端模板。后台使用 asyncio 协程定时采集，前端使用 Pico.css + Chart.js 渲染。

**技术栈：** FastAPI、aiosqlite、aiomysql、pydantic-settings、Jinja2、Pico.css、Chart.js

## 全局约束

- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写

---

## 文件结构

```
atlas-mysql-monitor/
├── main.py                          # FastAPI 入口、lifespan 事件
├── config.py                        # pydantic-settings 配置
├── database.py                      # SQLite 连接管理
├── collectors/
│   ├── __init__.py
│   └── mysql_collector.py           # MySQL 指标采集器
├── models/
│   ├── __init__.py
│   └── metrics.py                   # 指标 CRUD 操作
├── routes/
│   ├── __init__.py
│   ├── dashboard.py                 # 仪表盘页面路由
│   └── api.py                       # JSON API 路由
├── templates/
│   ├── base.html                    # 基础布局
│   └── dashboard.html               # 仪表盘页面
├── static/
│   └── css/
│       └── custom.css               # 自定义样式
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_metrics.py
│   └── test_collector.py
├── data/                            # 运行时生成
├── pyproject.toml
├── .env
├── .env.example
└── .gitignore
```

---

### Task 1: 项目配置与依赖

**文件：**
- 修改：`pyproject.toml`
- 创建：`.env.example`
- 创建：`.gitignore`
- 创建：`config.py`
- 创建：`tests/__init__.py`
- 创建：`tests/test_config.py`

**接口：**
- 产出：`Config` 类，供后续任务使用

- [ ] **Step 1: 更新 pyproject.toml 添加依赖**

```toml
[project]
name = "atlas-mysql-monitor"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.139.0",
    "uvicorn>=0.50.2",
    "aiosqlite>=0.20.0",
    "aiomysql>=0.2.0",
    "pydantic-settings>=2.0.0",
    "jinja2>=3.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 2: 同步依赖**

```bash
uv sync
```

预期输出：依赖安装成功

- [ ] **Step 3: 创建 .env.example**

```env
# MySQL 连接配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=monitor
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mysql

# 监控配置
COLLECT_INTERVAL=60
RETENTION_DAYS=30
```

- [ ] **Step 4: 创建 .gitignore**

```
.venv/
.env
data/
__pycache__/
*.pyc
.idea/
```

- [ ] **Step 5: 编写配置测试**

```python
# tests/test_config.py
import pytest
from config import Config


def test_config_default_values(monkeypatch):
    """测试配置默认值"""
    monkeypatch.setenv("MYSQL_HOST", "localhost")
    monkeypatch.setenv("MYSQL_USER", "test")
    monkeypatch.setenv("MYSQL_PASSWORD", "test")
    
    config = Config()
    assert config.MYSQL_HOST == "localhost"
    assert config.COLLECT_INTERVAL == 60
    assert config.RETENTION_DAYS == 30


def test_config_custom_values(monkeypatch):
    """测试自定义配置值"""
    monkeypatch.setenv("MYSQL_HOST", "192.168.1.100")
    monkeypatch.setenv("MYSQL_USER", "admin")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("COLLECT_INTERVAL", "30")
    monkeypatch.setenv("RETENTION_DAYS", "7")
    
    config = Config()
    assert config.MYSQL_HOST == "192.168.1.100"
    assert config.COLLECT_INTERVAL == 30
    assert config.RETENTION_DAYS == 7
```

- [ ] **Step 6: 运行测试验证失败**

```bash
uv run pytest tests/test_config.py -v
```

预期输出：FAIL（ModuleNotFoundError: No module named 'config'）

- [ ] **Step 7: 实现 config.py**

```python
# config.py
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # MySQL 连接配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "mysql"
    
    # 监控配置
    COLLECT_INTERVAL: int = 60  # 采集间隔（秒）
    RETENTION_DAYS: int = 30    # 数据保留天数
    
    class Config:
        env_file = ".env"


config = Config()
```

- [ ] **Step 8: 运行测试验证通过**

```bash
uv run pytest tests/test_config.py -v
```

预期输出：2 passed

- [ ] **Step 9: 提交代码**

```bash
git add pyproject.toml .env.example .gitignore config.py tests/
git commit -m "feat: 项目配置与依赖管理"
```

---

### Task 2: SQLite 数据库层

**文件：**
- 创建：`database.py`
- 创建：`tests/test_database.py`

**接口：**
- 产出：`init_db()`、`get_db()` 函数，供后续任务使用

- [ ] **Step 1: 编写数据库测试**

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

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_database.py -v
```

预期输出：FAIL（ModuleNotFoundError: No module named 'database'）

- [ ] **Step 3: 实现 database.py**

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

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_database.py -v
```

预期输出：2 passed

- [ ] **Step 5: 提交代码**

```bash
git add database.py tests/test_database.py
git commit -m "feat: SQLite 数据库层"
```

---

### Task 3: 指标数据模型

**文件：**
- 创建：`models/__init__.py`
- 创建：`models/metrics.py`
- 创建：`tests/test_metrics.py`

**接口：**
- 消费：`database.get_db()`
- 产出：`save_metrics()`、`get_latest_metrics()`、`get_metrics_history()`、`cleanup_old_metrics()` 函数

- [ ] **Step 1: 编写指标模型测试**

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

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_metrics.py -v
```

预期输出：FAIL（ModuleNotFoundError）

- [ ] **Step 3: 实现 models/metrics.py**

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

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_metrics.py -v
```

预期输出：3 passed

- [ ] **Step 5: 提交代码**

```bash
git add models/ tests/test_metrics.py
git commit -m "feat: 指标数据模型"
```

---

### Task 4: MySQL 采集器

**文件：**
- 创建：`collectors/__init__.py`
- 创建：`collectors/mysql_collector.py`
- 创建：`tests/test_collector.py`

**接口：**
- 消费：`config.Config`
- 产出：`MySQLCollector` 类，提供 `collect()` 方法

- [ ] **Step 1: 编写采集器测试**

```python
# tests/test_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from collectors.mysql_collector import MySQLCollector


@pytest.fixture
def mock_config():
    """模拟配置"""
    config = MagicMock()
    config.MYSQL_HOST = "localhost"
    config.MYSQL_PORT = 3306
    config.MYSQL_USER = "test"
    config.MYSQL_PASSWORD = "test"
    config.MYSQL_DATABASE = "mysql"
    return config


@pytest.mark.asyncio
async def test_collector_parse_status(mock_config):
    """测试解析 MySQL 状态"""
    collector = MySQLCollector(mock_config)
    
    # 模拟 SHOW GLOBAL STATUS 返回
    status_data = {
        "Threads_connected": "10",
        "Threads_running": "2",
        "Uptime": "3600",
        "Slow_queries": "5",
        "Com_select": "1000",
        "Com_insert": "100",
        "Com_update": "50",
        "Com_delete": "10",
    }
    
    metrics = collector._parse_status(status_data)
    
    assert metrics["threads_connected"] == 10
    assert metrics["threads_running"] == 2
    assert metrics["uptime"] == 3600
    assert metrics["slow_queries"] == 5
    assert metrics["com_select"] == 1000


@pytest.mark.asyncio
async def test_collector_calculate_qps(mock_config):
    """测试计算 QPS"""
    collector = MySQLCollector(mock_config)
    
    current = {
        "com_select": 1060,
        "com_insert": 110,
        "com_update": 55,
        "com_delete": 12,
    }
    
    previous = {
        "com_select": 1000,
        "com_insert": 100,
        "com_update": 50,
        "com_delete": 10,
    }
    
    interval = 60  # 秒
    
    qps = collector._calculate_qps(current, previous, interval)
    
    assert qps["select_qps"] == pytest.approx(1.0)
    assert qps["insert_qps"] == pytest.approx(0.1667, rel=0.01)
    assert qps["update_qps"] == pytest.approx(0.0833, rel=0.01)
    assert qps["delete_qps"] == pytest.approx(0.0333, rel=0.01)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_collector.py -v
```

预期输出：FAIL（ModuleNotFoundError）

- [ ] **Step 3: 实现 collectors/mysql_collector.py**

```python
# collectors/mysql_collector.py
import aiomysql
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MySQLCollector:
    """MySQL 指标采集器"""
    
    def __init__(self, config):
        self.config = config
        self.pool: Optional[aiomysql.Pool] = None
    
    async def connect(self):
        """创建连接池"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                db=self.config.MYSQL_DATABASE,
                minsize=1,
                maxsize=2,
            )
            logger.info("MySQL 连接池创建成功")
        except Exception as e:
            logger.error(f"MySQL 连接失败: {e}")
            raise
    
    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
    
    async def collect(self) -> Dict[str, Any]:
        """采集 MySQL 指标"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW GLOBAL STATUS")
                rows = await cursor.fetchall()
                status_data = {row[0]: row[1] for row in rows}
        
        metrics = self._parse_status(status_data)
        return metrics
    
    def _parse_status(self, status_data: Dict[str, str]) -> Dict[str, Any]:
        """解析 MySQL 状态数据"""
        return {
            "threads_connected": int(status_data.get("Threads_connected", 0)),
            "threads_running": int(status_data.get("Threads_running", 0)),
            "uptime": int(status_data.get("Uptime", 0)),
            "slow_queries": int(status_data.get("Slow_queries", 0)),
            "com_select": int(status_data.get("Com_select", 0)),
            "com_insert": int(status_data.get("Com_insert", 0)),
            "com_update": int(status_data.get("Com_update", 0)),
            "com_delete": int(status_data.get("Com_delete", 0)),
        }
    
    def _calculate_qps(
        self, current: Dict[str, int], previous: Dict[str, int], interval: int
    ) -> Dict[str, float]:
        """计算各类 QPS"""
        return {
            "select_qps": (current["com_select"] - previous["com_select"]) / interval,
            "insert_qps": (current["com_insert"] - previous["com_insert"]) / interval,
            "update_qps": (current["com_update"] - previous["com_update"]) / interval,
            "delete_qps": (current["com_delete"] - previous["com_delete"]) / interval,
        }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_collector.py -v
```

预期输出：2 passed

- [ ] **Step 5: 提交代码**

```bash
git add collectors/ tests/test_collector.py
git commit -m "feat: MySQL 采集器"
```

---

### Task 5: FastAPI 主应用与后台任务

**文件：**
- 修改：`main.py`

**接口：**
- 消费：`config.config`、`database.init_db()`、`models.metrics`、`collectors.mysql_collector.MySQLCollector`

- [ ] **Step 1: 重写 main.py**

```python
# main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import config
from database import init_db, DEFAULT_DB_PATH
from models.metrics import save_metrics, get_latest_metrics, cleanup_old_metrics
from collectors.mysql_collector import MySQLCollector
from routes import dashboard, api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局状态
collector: MySQLCollector = None
collect_task: asyncio.Task = None
consecutive_failures: int = 0
last_success_time: str = None


async def collect_loop():
    """后台采集循环"""
    global consecutive_failures, last_success_time
    
    previous_metrics = None
    
    while True:
        try:
            # 采集当前指标
            current_metrics = await collector.collect()
            
            # 计算 QPS
            if previous_metrics:
                qps = collector._calculate_qps(
                    current_metrics,
                    previous_metrics,
                    config.COLLECT_INTERVAL
                )
                current_metrics.update(qps)
            else:
                # 首次采集，QPS 为 None
                current_metrics.update({
                    "select_qps": None,
                    "insert_qps": None,
                    "update_qps": None,
                    "delete_qps": None,
                })
            
            # 保存到数据库
            await save_metrics(str(DEFAULT_DB_PATH), current_metrics)
            
            # 更新状态
            previous_metrics = current_metrics
            consecutive_failures = 0
            last_success_time = current_metrics.get("timestamp")
            
            logger.info("指标采集成功")
            
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"采集失败（连续失败 {consecutive_failures} 次）: {e}")
        
        await asyncio.sleep(config.COLLECT_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global collector, collect_task
    
    # 启动时初始化
    logger.info("正在初始化数据库...")
    await init_db()
    
    # 清理过期数据
    deleted = await cleanup_old_metrics(str(DEFAULT_DB_PATH), config.RETENTION_DAYS)
    if deleted > 0:
        logger.info(f"已清理 {deleted} 条过期数据")
    
    # 创建采集器
    logger.info("正在连接 MySQL...")
    collector = MySQLCollector(config)
    
    # 启动后台采集任务
    logger.info(f"启动后台采集任务（间隔 {config.COLLECT_INTERVAL} 秒）...")
    collect_task = asyncio.create_task(collect_loop())
    
    yield
    
    # 关闭时清理
    if collect_task:
        collect_task.cancel()
        try:
            await collect_task
        except asyncio.CancelledError:
            pass
    
    if collector:
        await collector.close()
    
    logger.info("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(title="Atlas MySQL Monitor", lifespan=lifespan)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(dashboard.router)
app.include_router(api.router)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
```

- [ ] **Step 2: 运行应用验证启动**

```bash
uv run uvicorn main:app --reload
```

预期输出：应用启动成功，监听 8000 端口（会因为没有 .env 文件和 MySQL 连接失败而报错，这是预期的）

- [ ] **Step 3: 提交代码**

```bash
git add main.py
git commit -m "feat: FastAPI 主应用与后台采集任务"
```

---

### Task 6: API 路由

**文件：**
- 创建：`routes/__init__.py`
- 创建：`routes/api.py`

**接口：**
- 消费：`models.metrics.get_latest_metrics()`、`models.metrics.get_metrics_history()`
- 产出：`GET /api/status`、`GET /api/metrics`

- [ ] **Step 1: 实现 routes/api.py**

```python
# routes/api.py
from fastapi import APIRouter, Query
from models.metrics import get_latest_metrics, get_metrics_history
from database import DEFAULT_DB_PATH

router = APIRouter(prefix="/api")


@router.get("/status")
async def get_status():
    """获取最新状态（用于顶部卡片）"""
    metrics = await get_latest_metrics(str(DEFAULT_DB_PATH))
    
    if not metrics:
        return {
            "connected": False,
            "message": "等待首次数据采集...",
            "threads_connected": "--",
            "threads_running": "--",
            "uptime": "--",
            "slow_queries": "--",
            "total_qps": "--",
            "last_update": None,
        }
    
    # 计算总 QPS
    total_qps = 0
    if metrics.get("select_qps") is not None:
        total_qps = (
            metrics["select_qps"]
            + metrics["insert_qps"]
            + metrics["update_qps"]
            + metrics["delete_qps"]
        )
    
    # 格式化运行时间
    uptime_seconds = metrics["uptime"]
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    uptime_str = f"{days}d {hours}h"
    
    return {
        "connected": True,
        "message": "MySQL 运行中",
        "threads_connected": metrics["threads_connected"],
        "threads_running": metrics["threads_running"],
        "uptime": uptime_str,
        "slow_queries": metrics["slow_queries"],
        "total_qps": round(total_qps, 2),
        "last_update": metrics["timestamp"],
    }


@router.get("/metrics")
async def get_metrics(hours: int = Query(default=24, ge=1, le=168)):
    """获取指标历史数据（用于图表）"""
    history = await get_metrics_history(str(DEFAULT_DB_PATH), hours)
    
    return {
        "timestamps": [m["timestamp"] for m in history],
        "select_qps": [m["select_qps"] for m in history],
        "insert_qps": [m["insert_qps"] for m in history],
        "update_qps": [m["update_qps"] for m in history],
        "delete_qps": [m["delete_qps"] for m in history],
        "threads_connected": [m["threads_connected"] for m in history],
        "threads_running": [m["threads_running"] for m in history],
    }
```

- [ ] **Step 2: 运行应用验证路由**

```bash
uv run uvicorn main:app --reload
```

访问 `http://localhost:8000/docs` 应该能看到 API 文档

- [ ] **Step 3: 提交代码**

```bash
git add routes/
git commit -m "feat: API 路由"
```

---

### Task 7: 仪表盘页面路由与模板

**文件：**
- 创建：`routes/dashboard.py`
- 创建：`templates/base.html`
- 创建：`templates/dashboard.html`

**接口：**
- 消费：FastAPI、Jinja2
- 产出：`GET /` 返回 HTML 页面

- [ ] **Step 1: 实现 routes/dashboard.py**

```python
# routes/dashboard.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def dashboard(request: Request):
    """仪表盘页面"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
```

- [ ] **Step 2: 创建 templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Atlas MySQL Monitor{% endblock %}</title>
    
    <!-- Pico.css -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    
    <!-- 自定义样式 -->
    <link rel="stylesheet" href="/static/css/custom.css">
</head>
<body>
    <header class="container">
        <nav>
            <ul>
                <li><strong>Atlas MySQL Monitor</strong></li>
            </ul>
            <ul>
                <li>
                    <a href="#" id="theme-toggle" class="outline" role="button">
                        <span id="theme-icon">🌙</span>
                    </a>
                </li>
            </ul>
        </nav>
    </header>
    
    <main class="container">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="container">
        <small>Atlas MySQL Monitor v0.1.0</small>
    </footer>
    
    {% block scripts %}{% endblock %}
    
    <!-- 主题切换脚本 -->
    <script>
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        const html = document.documentElement;
        
        // 从 localStorage 读取主题
        const savedTheme = localStorage.getItem('theme') || 'light';
        html.setAttribute('data-theme', savedTheme);
        themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        
        themeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        });
    </script>
</body>
</html>
```

- [ ] **Step 3: 创建 templates/dashboard.html**

```html
{% extends "base.html" %}

{% block title %}仪表盘 - Atlas MySQL Monitor{% endblock %}

{% block content %}
<!-- 警告横幅 -->
<div id="warning-banner" class="warning-banner" style="display: none;">
    <article>
        <p id="warning-message"></p>
    </article>
</div>

<!-- 状态卡片 -->
<section id="status-section">
    <div class="grid">
        <article>
            <header>状态</header>
            <p id="mysql-status">加载中...</p>
        </article>
        <article>
            <header>运行时间</header>
            <p id="mysql-uptime">--</p>
        </article>
        <article>
            <header>最后采集</header>
            <p id="last-update">--</p>
        </article>
    </div>
</section>

<!-- 指标卡片 -->
<section id="metrics-cards">
    <div class="grid">
        <article>
            <header>连接数</header>
            <p id="threads-connected" class="metric-value">--</p>
        </article>
        <article>
            <header>活跃线程</header>
            <p id="threads-running" class="metric-value">--</p>
        </article>
        <article>
            <header>慢查询</header>
            <p id="slow-queries" class="metric-value">--</p>
        </article>
        <article>
            <header>总 QPS</header>
            <p id="total-qps" class="metric-value">--</p>
        </article>
    </div>
</section>

<!-- QPS 趋势图 -->
<section id="qps-chart-section">
    <article>
        <header>QPS 趋势（最近 24 小时）</header>
        <canvas id="qpsChart"></canvas>
    </article>
</section>

<!-- 连接数趋势图 -->
<section id="connections-chart-section">
    <article>
        <header>连接数趋势（最近 24 小时）</header>
        <canvas id="connectionsChart"></canvas>
    </article>
</section>
{% endblock %}

{% block scripts %}
<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>

<script>
    // 图表实例
    let qpsChart = null;
    let connectionsChart = null;
    
    // 初始化图表
    function initCharts() {
        const qpsCtx = document.getElementById('qpsChart').getContext('2d');
        qpsChart = new Chart(qpsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'SELECT QPS',
                        data: [],
                        borderColor: '#3b82f6',
                        tension: 0.1
                    },
                    {
                        label: 'INSERT QPS',
                        data: [],
                        borderColor: '#22c55e',
                        tension: 0.1
                    },
                    {
                        label: 'UPDATE QPS',
                        data: [],
                        borderColor: '#f97316',
                        tension: 0.1
                    },
                    {
                        label: 'DELETE QPS',
                        data: [],
                        borderColor: '#ef4444',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        const connCtx = document.getElementById('connectionsChart').getContext('2d');
        connectionsChart = new Chart(connCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '连接数',
                        data: [],
                        borderColor: '#8b5cf6',
                        tension: 0.1
                    },
                    {
                        label: '活跃线程',
                        data: [],
                        borderColor: '#06b6d4',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // 更新状态卡片
    async function updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            document.getElementById('mysql-status').textContent = data.message;
            document.getElementById('mysql-uptime').textContent = data.uptime;
            document.getElementById('last-update').textContent = data.last_update || '--';
            document.getElementById('threads-connected').textContent = data.threads_connected;
            document.getElementById('threads-running').textContent = data.threads_running;
            document.getElementById('slow-queries').textContent = data.slow_queries;
            document.getElementById('total-qps').textContent = data.total_qps;
            
            // 处理警告横幅
            const banner = document.getElementById('warning-banner');
            if (!data.connected && data.last_update) {
                banner.style.display = 'block';
                document.getElementById('warning-message').textContent = 
                    `MySQL 连接异常，最后成功采集时间: ${data.last_update}`;
            } else {
                banner.style.display = 'none';
            }
        } catch (error) {
            console.error('获取状态失败:', error);
        }
    }
    
    // 更新图表
    async function updateCharts() {
        try {
            const response = await fetch('/api/metrics?hours=24');
            const data = await response.json();
            
            // 格式化时间标签
            const labels = data.timestamps.map(t => {
                const date = new Date(t);
                return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            });
            
            // 更新 QPS 图表
            qpsChart.data.labels = labels;
            qpsChart.data.datasets[0].data = data.select_qps;
            qpsChart.data.datasets[1].data = data.insert_qps;
            qpsChart.data.datasets[2].data = data.update_qps;
            qpsChart.data.datasets[3].data = data.delete_qps;
            qpsChart.update();
            
            // 更新连接数图表
            connectionsChart.data.labels = labels;
            connectionsChart.data.datasets[0].data = data.threads_connected;
            connectionsChart.data.datasets[1].data = data.threads_running;
            connectionsChart.update();
        } catch (error) {
            console.error('获取指标失败:', error);
        }
    }
    
    // 页面加载后初始化
    document.addEventListener('DOMContentLoaded', () => {
        initCharts();
        updateStatus();
        updateCharts();
        
        // 每 60 秒刷新一次
        setInterval(() => {
            updateStatus();
            updateCharts();
        }, 60000);
    });
</script>
{% endblock %}
```

- [ ] **Step 4: 运行应用验证页面**

```bash
uv run uvicorn main:app --reload
```

访问 `http://localhost:8000/` 应该能看到仪表盘页面（数据为空状态）

- [ ] **Step 5: 提交代码**

```bash
git add routes/dashboard.py templates/
git commit -m "feat: 仪表盘页面"
```

---

### Task 8: 自定义样式

**文件：**
- 创建：`static/css/custom.css`

- [ ] **Step 1: 创建 custom.css**

```css
/* static/css/custom.css */

/* 指标数值样式 */
.metric-value {
    font-size: 2rem;
    font-weight: bold;
    text-align: center;
    margin: 0;
}

/* 警告横幅 */
.warning-banner article {
    background-color: #fef3c7;
    border-left: 4px solid #f59e0b;
}

/* 暗色主题下的警告横幅 */
[data-theme="dark"] .warning-banner article {
    background-color: #451a03;
    border-left-color: #f59e0b;
}

/* 图表容器 */
canvas {
    max-height: 300px;
}

/* 状态卡片网格 */
.grid article {
    margin-bottom: 0;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .metric-value {
        font-size: 1.5rem;
    }
}
```

- [ ] **Step 2: 提交代码**

```bash
git add static/
git commit -m "feat: 自定义样式"
```

---

### Task 9: 创建 .env 文件并测试完整流程

**文件：**
- 创建：`.env`

- [ ] **Step 1: 创建 .env 文件**

```env
# MySQL 连接配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=monitor
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mysql

# 监控配置
COLLECT_INTERVAL=60
RETENTION_DAYS=30
```

- [ ] **Step 2: 启动应用测试完整流程**

```bash
uv run uvicorn main:app --reload
```

预期行为：
1. 应用启动，自动创建 `data/monitor.db`
2. 尝试连接 MySQL（会失败，因为没有真实的 MySQL）
3. 访问 `http://localhost:8000/` 看到空状态仪表盘
4. 查看日志中的采集失败信息

- [ ] **Step 3: 运行所有测试**

```bash
uv run pytest tests/ -v
```

预期输出：所有测试通过

- [ ] **Step 4: 最终提交**

```bash
git add .env
git commit -m "feat: 完成 MVP 版本"
```

---

## 自检清单

- [x] **规格覆盖**：所有规格要求都有对应任务
- [x] **占位符扫描**：无 TBD、TODO 或模糊要求
- [x] **类型一致性**：函数名、参数类型在整个计划中保持一致
- [x] **代码完整性**：每个步骤都包含完整代码
- [x] **测试覆盖**：每个核心模块都有测试

---

## 执行选项

计划已完成并保存到 `docs/superpowers/plans/2026-07-07-atlas-mysql-monitor.md`。

**两种执行方式：**

**1. 子智能体驱动（推荐）** - 每个任务派发一个新的子智能体，任务间有审查，迭代快

**2. 内置执行** - 在当前会话中使用 executing-plans 执行任务，批量执行带检查点

**你选择哪种方式？**
