# Task 3 实施报告

## 状态
DONE

## 提交记录
- `fad3414` feat: 指标数据模型

## 文件清单
- 创建：`models/__init__.py`（空的包初始化文件）
- 创建：`models/metrics.py`（4 个异步 CRUD 函数）
- 创建：`tests/test_metrics.py`（3 个测试用例）

## 接口实现
| 函数 | 说明 |
|------|------|
| `save_metrics(db_path, metrics)` | 保存一条指标记录到 mysql_metrics 表 |
| `get_latest_metrics(db_path)` | 按 id 降序获取最新一条指标 |
| `get_metrics_history(db_path, hours=24)` | 获取最近 N 小时内的指标历史 |
| `cleanup_old_metrics(db_path, retention_days=30)` | 清理超过保留天数的旧数据，返回删除行数 |

## 测试结果
```
$ uv run pytest tests/test_metrics.py -v

tests/test_metrics.py::test_save_and_get_latest_metrics PASSED
tests/test_metrics.py::test_get_metrics_history PASSED
tests/test_metrics.py::test_cleanup_old_metrics PASSED

3 passed in 0.27s
```

全量测试（含 Task 1 和 Task 2 的测试）：
```
$ uv run pytest -v

tests/test_config.py::test_config_default_values PASSED
tests/test_config.py::test_config_custom_values PASSED
tests/test_database.py::test_init_db_creates_table PASSED
tests/test_database.py::test_get_db_returns_connection PASSED
tests/test_metrics.py::test_save_and_get_latest_metrics PASSED
tests/test_metrics.py::test_get_metrics_history PASSED
tests/test_metrics.py::test_cleanup_old_metrics PASSED

7 passed in 0.58s
```

## 自检
- 所有函数均为 `async def` + `await`，符合项目约束
- 每个函数独立创建数据库连接，传入 `db_path` 字符串而非连接对象
- 使用 `aiosqlite.Row` 作为 `row_factory`，返回 `dict` 便于后续 JSON 序列化
- 测试使用 `tmp_path` 隔离，无副作用

## 关注点
- 原始任务简报中的测试使用 `@pytest.fixture` 装饰异步 fixture，在 `pytest-asyncio` strict 模式下会报错。已修复为 `@pytest_asyncio.fixture`，并在测试文件中添加了 `import pytest_asyncio`。
- `models/metrics.py` 顶部和各函数内部均有一行 `import aiosqlite`（顶部为顶层导入，函数内为重复导入）。这是任务简报中原始代码的写法，保持不变以免偏离规格。如需清理可在后续任务中统一处理。
