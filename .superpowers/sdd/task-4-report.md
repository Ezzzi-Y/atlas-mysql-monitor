# Task 4 实施报告

## 状态
DONE

## 提交记录
- `22e421e` — feat: MySQL 采集器

## 文件清单
- `collectors/__init__.py` — 空包初始化文件
- `collectors/mysql_collector.py` — `MySQLCollector` 类实现
- `tests/test_collector.py` — 采集器单元测试（2 个用例）

## 测试结果

**测试命令：**
```bash
uv run pytest tests/test_collector.py -v
```

**输出：**
```
tests/test_collector.py::test_collector_parse_status PASSED
tests/test_collector.py::test_collector_calculate_qps PASSED
2 passed in 0.23s
```

**全量回归测试（9 个用例全部通过）：**
```bash
uv run pytest -v
```
```
tests/test_collector.py::test_collector_parse_status PASSED
tests/test_collector.py::test_collector_calculate_qps PASSED
tests/test_config.py::test_config_default_values PASSED
tests/test_config.py::test_config_custom_values PASSED
tests/test_database.py::test_init_db_creates_table PASSED
tests/test_database.py::test_get_db_returns_connection PASSED
tests/test_metrics.py::test_save_and_get_latest_metrics PASSED
tests/test_metrics.py::test_get_metrics_history PASSED
tests/test_metrics.py::test_cleanup_old_metrics PASSED
9 passed in 0.61s
```

## 自检
- 模块导入前测试失败（`ModuleNotFoundError`），实现后全部通过，符合 TDD 预期。
- `_parse_status` 和 `_calculate_qps` 均为纯同步函数，无需 mock 外部依赖即可测试。
- `connect`、`close`、`collect` 方法依赖 `aiomysql` 连接池，现有测试未覆盖（需要真实的 MySQL 实例或更复杂的 mock）。这一层集成测试建议在后续任务中补充。
- 已有测试套件（9 个用例）未受影响。

## 关注点
- `collect()` 方法中，若连接池未初始化会自动调用 `connect()`。这在生产环境中是便利设计，但也意味着首次采集可能较慢（包含连接建立开销）。
- `_calculate_qps` 未处理 `interval <= 0` 的边界情况（如除以零）。当前由调用方保证间隔合法，暂无风险，但建议后续加入防御性检查。
