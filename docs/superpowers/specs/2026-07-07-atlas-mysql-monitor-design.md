# Atlas MySQL Monitor — 设计文档

## 项目概述

基于 FastAPI 的 MySQL 监控工具，做简单的指标统计。采用服务端渲染 Web 架构，SQLite 存储数据。不追求 Prometheus 级别的能力，专注基础状态监控。

## 需求总结

- **监控范围**：基础 MySQL 状态（连接数、QPS、慢查询、运行时间）
- **采集方式**：后端定时采集，每分钟一次（可配置）
- **监控实例**：单实例
- **数据保留**：可配置天数（默认 30 天）
- **告警能力**：暂不做，先做 MVP
- **前端风格**：简约、高级感，Classless CSS（Pico.css）+ Chart.js
- **主题模式**：双主题切换（亮色/暗色）

---

## 架构设计

### 目录结构

```
atlas-mysql-monitor/
├── main.py                 # FastAPI 应用入口、lifespan 事件
├── config.py               # 配置管理（从 .env 读取）
├── database.py             # SQLite 数据库初始化与连接管理
├── collectors/
│   └── mysql_collector.py  # MySQL 指标采集器
├── models/
│   └── metrics.py          # 指标数据模型与 CRUD 操作
├── routes/
│   ├── dashboard.py        # 仪表盘页面路由
│   └── api.py              # 图表数据 API（JSON）
├── templates/
│   ├── base.html           # 基础布局模板
│   ├── dashboard.html      # 仪表盘页面
│   └── partials/           # 可复用模板片段
├── static/
│   └── css/
│       └── custom.css      # 自定义样式（与 Pico.css 配合）
├── data/
│   └── monitor.db          # SQLite 数据库文件（运行时生成）
├── pyproject.toml
├── .env                    # MySQL 连接配置、采集间隔、保留天数
└── .env.example
```

### 模块职责

- **main.py**：创建 FastAPI 实例、注册路由、在 lifespan 中启动/停止后台采集任务
- **config.py**：用 pydantic-settings 管理配置（MySQL 连接、采集间隔、保留天数）
- **database.py**：SQLite 异步连接管理、建表
- **collectors/mysql_collector.py**：用 `aiomysql` 连接 MySQL 执行 `SHOW GLOBAL STATUS` 采集指标
- **models/metrics.py**：指标的写入、查询、清理逻辑
- **routes/api.py**：返回 JSON 数据给 Chart.js
- **routes/dashboard.py**：返回 Jinja2 渲染的 HTML 页面

### 技术栈

- **框架**：FastAPI
- **服务器**：Uvicorn（ASGI）
- **包管理器**：uv
- **Python**：>=3.12
- **数据库**：SQLite（通过 `aiosqlite`）
- **MySQL 客户端**：`aiomysql`
- **模板引擎**：Jinja2
- **CSS 框架**：Pico.css（classless）
- **图表库**：Chart.js（CDN）
- **配置管理**：pydantic-settings

---

## 数据库设计

### 表结构：`mysql_metrics`

```sql
CREATE TABLE mysql_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    -- 基础状态
    threads_connected INTEGER,   -- 当前连接数
    threads_running INTEGER,     -- 活跃线程数
    uptime INTEGER,              -- MySQL 运行时间（秒）
    slow_queries INTEGER,        -- 慢查询总数（Com_slow_queries）
    -- CRUD 计数（绝对值，用于计算 QPS）
    com_select INTEGER,
    com_insert INTEGER,
    com_update INTEGER,
    com_delete INTEGER,
    -- 派生指标（采集时计算）
    select_qps REAL,
    insert_qps REAL,
    update_qps REAL,
    delete_qps REAL
);

CREATE INDEX idx_timestamp ON mysql_metrics(timestamp);
```

### QPS 计算方式

- 采集 `SHOW GLOBAL STATUS` 中的 `Com_select`、`Com_insert`、`Com_update`、`Com_delete` 绝对值
- 与上一条记录做差，除以采集间隔秒数，分别得到四类 QPS
- 首次采集时无上一条记录，QPS 字段存 NULL

### 数据清理

- 应用启动时执行一次清理，删除超过 `RETENTION_DAYS` 的旧数据
- 默认保留 30 天，可通过 `.env` 配置

---

## 后台采集机制

### 启动流程（FastAPI lifespan）

```
应用启动
  → 初始化 SQLite 数据库（建表 + 清理过期数据）
  → 启动后台采集协程
  → 应用就绪，开始处理请求

应用关闭
  → 取消后台采集协程
  → 关闭数据库连接
```

### 采集协程逻辑

```python
async def collect_loop():
    while True:
        try:
            # 1. 连接 MySQL，执行 SHOW GLOBAL STATUS
            # 2. 读取上一条记录，计算各类 QPS
            # 3. 写入 SQLite
        except Exception as e:
            logger.error(f"采集失败: {e}")
        await asyncio.sleep(config.COLLECT_INTERVAL)
```

### 关键设计点

- 使用 `asyncio.create_task` 在 lifespan 中启动，lifespan 结束时自动取消
- 采集失败只记录日志，不影响应用运行
- MySQL 连接使用连接池（aiomysql），避免每次采集都重新建连
- 首次采集时没有上一条记录，QPS 字段存 NULL
- 采集间隔从 `.env` 配置文件读取，启动后修改需重启应用

---

## Web UI 设计

### 页面布局

```
┌─────────────────────────────────────────────────┐
│  Atlas MySQL Monitor          [🌙/☀️] 主题切换  │
├─────────────────────────────────────────────────┤
│  ● MySQL 运行中  │  运行时间: 15d 3h  │  最后采集: 14:32  │
├─────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 连接数   │ │ 活跃线程 │ │ 慢查询   │ │ 总 QPS   │  │
│  │   12     │ │    3     │ │    5     │ │  156.2   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────┤
│  QPS 趋势图（Chart.js 折线图，最近 24 小时）       │
│  - SELECT QPS（蓝色）                              │
│  - INSERT QPS（绿色）                              │
│  - UPDATE QPS（橙色）                              │
│  - DELETE QPS（红色）                              │
├─────────────────────────────────────────────────┤
│  连接数趋势图（Chart.js 折线图，最近 24 小时）      │
│  - threads_connected（紫色）                       │
│  - threads_running（青色）                         │
└─────────────────────────────────────────────────┘
```

### 技术实现

- **CSS 框架**：Pico.css（classless，自动美化语义化标签）
- **图表库**：Chart.js（CDN 引入）
- **主题切换**：`<html data-theme="dark/light">` + Pico.css 内置主题支持 + 少量 JS 切换逻辑
- **数据更新**：前端定时 AJAX 请求（默认 60 秒）

### API 接口

- `GET /api/metrics?hours=24` — 返回最近 N 小时的指标数据（JSON 数组）
- `GET /api/status` — 返回最新一条指标（用于顶部卡片）

---

## 配置管理

### .env 文件

```env
# MySQL 连接配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=monitor
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mysql

# 监控配置
COLLECT_INTERVAL=60        # 采集间隔（秒），默认 60
RETENTION_DAYS=30          # 数据保留天数，默认 30
```

### 配置加载

使用 `pydantic-settings` 的 `BaseSettings` 类，自动从 `.env` 文件和环境变量读取配置。

---

## 错误处理

### MySQL 连接失败

- 采集时连接失败：记录日志，跳过本次采集，等待下次
- 连续失败 3 次：在仪表盘顶部显示警告横幅（"MySQL 连接异常，最后成功采集时间: ..."）
- 连续失败计数在内存中维护（应用重启后重置），每次采集成功后归零
- 恢复后自动消除警告

### 首次启动（无数据）

- 仪表盘显示空状态提示："等待首次数据采集..."
- QPS 字段显示为 "--"

### SQLite 文件不存在

- 启动时自动创建 `data/` 目录和 `monitor.db` 文件
- 自动建表，无需手动初始化

### 页面刷新失败

- 前端 AJAX 请求失败时，在图表区域显示 "数据加载失败，请刷新页面"

---

## 依赖清单

```
fastapi>=0.139.0
uvicorn>=0.50.2
aiosqlite>=0.20.0
aiomysql>=0.2.0
pydantic-settings>=2.0.0
jinja2>=3.1.0
python-dotenv>=1.0.0
```
