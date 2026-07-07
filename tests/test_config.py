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
