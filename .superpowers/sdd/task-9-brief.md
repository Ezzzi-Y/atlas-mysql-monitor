# Task 9: 创建 .env 文件并测试完整流程

## 任务目标
创建 .env 配置文件并测试完整应用流程。

## 文件清单
- 创建：`.env`

## 详细步骤

### Step 1: 创建 .env 文件
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

### Step 2: 启动应用测试完整流程
```bash
uv run uvicorn main:app --reload
```
预期行为：
1. 应用启动，自动创建 `data/monitor.db`
2. 尝试连接 MySQL（会失败，因为没有真实的 MySQL）
3. 访问 `http://localhost:8000/` 看到空状态仪表盘
4. 查看日志中的采集失败信息

### Step 3: 运行所有测试
```bash
uv run pytest tests/ -v
```
预期输出：所有测试通过

### Step 4: 最终提交
```bash
git add .env
git commit -m "feat: 完成 MVP 版本"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
