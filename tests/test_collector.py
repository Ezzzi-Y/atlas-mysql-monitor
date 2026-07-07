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
