# Task 4: MySQL 采集器

## 任务目标
创建 MySQL 指标采集器模块，负责连接 MySQL 并采集基础状态指标。

## 文件清单
- 创建：`collectors/__init__.py`
- 创建：`collectors/mysql_collector.py`
- 创建：`tests/test_collector.py`

## 接口产出
- `MySQLCollector` 类：
  - `__init__(self, config)`: 初始化采集器
  - `connect(self)`: 创建连接池
  - `close(self)`: 关闭连接池
  - `collect(self)`: 采集 MySQL 指标
  - `_parse_status(self, status_data)`: 解析 MySQL 状态数据
  - `_calculate_qps(self, current, previous, interval)`: 计算各类 QPS

## 详细步骤

### Step 1: 编写采集器测试
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

### Step 2: 运行测试验证失败
```bash
uv run pytest tests/test_collector.py -v
```
预期输出：FAIL（ModuleNotFoundError）

### Step 3: 实现 collectors/mysql_collector.py
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

### Step 4: 运行测试验证通过
```bash
uv run pytest tests/test_collector.py -v
```
预期输出：2 passed

### Step 5: 提交代码
```bash
git add collectors/ tests/test_collector.py
git commit -m "feat: MySQL 采集器"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
