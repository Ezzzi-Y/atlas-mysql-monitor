# Task 1: 项目配置与依赖

## 任务目标
配置项目基础依赖和开发环境，创建配置管理模块。

## 文件清单
- 修改：`pyproject.toml`
- 创建：`.env.example`
- 创建：`.gitignore`
- 创建：`config.py`
- 创建：`tests/__init__.py`
- 创建：`tests/test_config.py`

## 接口产出
- `Config` 类：使用 pydantic-settings 管理配置，供后续任务使用
- 配置项：MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, COLLECT_INTERVAL, RETENTION_DAYS

## 详细步骤

### Step 1: 更新 pyproject.toml 添加依赖
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

### Step 2: 同步依赖
```bash
uv sync
```

### Step 3: 创建 .env.example
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

### Step 4: 创建 .gitignore
```
.venv/
.env
data/
__pycache__/
*.pyc
.idea/
```

### Step 5: 编写配置测试
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

### Step 6: 运行测试验证失败
```bash
uv run pytest tests/test_config.py -v
```
预期输出：FAIL（ModuleNotFoundError: No module named 'config'）

### Step 7: 实现 config.py
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

### Step 8: 运行测试验证通过
```bash
uv run pytest tests/test_config.py -v
```
预期输出：2 passed

### Step 9: 提交代码
```bash
git add pyproject.toml .env.example .gitignore config.py tests/
git commit -m "feat: 项目配置与依赖管理"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
