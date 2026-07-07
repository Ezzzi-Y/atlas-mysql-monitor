# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在本仓库中工作提供指导。

## 语言要求

- 当用户提问时，必须使用中文回答
- 所有文档（包括 CLAUDE.md、README、注释等）必须使用中文编写

## 项目概述

Atlas MySQL Monitor — 基于 FastAPI 的 MySQL 监控工具。做简单的指标统计（不追求 Prometheus 级别的能力），采用服务端渲染 Web 架构（不做前后端分离），使用 SQLite 存储数据。

## 技术栈

- **框架**：FastAPI（异步 Python Web 框架）
- **服务器**：Uvicorn（ASGI）
- **包管理器**：uv（非 pip/poetry）
- **Python**：>=3.12
- **数据库**：SQLite（通过 `aiosqlite` 等异步驱动）
- **模板引擎**：Jinja2（用于 SSR）

## 常用命令

```bash
# 启动开发服务器（热重载）
uv run uvicorn main:app --reload

# 启动开发服务器（替代方式）
uv run fastapi dev main.py

# 安装依赖
uv sync

# 添加依赖
uv add <package>

# 运行测试
uv run pytest

# 运行单个测试
uv run pytest tests/test_<name>.py::test_<function>
```

## 架构

- **SSR 模式**：路由返回 `TemplateResponse`（Jinja2 HTML），而非 JSON API（AJAX 数据接口除外）
- **单进程**：本地使用，无需 worker 编排
- **SQLite**：基于本地文件的数据库，无需外部数据库配置
- **静态文件**：由 FastAPI 的 `StaticFiles` 中间件在 `/static` 路径下提供服务

## 关键约定

- 所有指标采集逻辑放在独立模块中（如 `collectors/`）
- 数据库模型/查询使用异步模式（`async def`、`await`）
- HTML 模板放在 `templates/` 目录，静态资源放在 `static/`
- 配置通过环境变量或 `.env` 文件管理
