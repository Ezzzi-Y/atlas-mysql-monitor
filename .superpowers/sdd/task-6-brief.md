# Task 6: API 路由

## 任务目标
实现 API 路由，提供 JSON 接口供前端图表使用。

## 文件清单
- 修改：`routes/api.py`（Task 5 已创建占位文件）

## 接口产出
- `GET /api/status`: 获取最新状态（用于顶部卡片）
- `GET /api/metrics`: 获取指标历史数据（用于图表）

## 详细步骤

### Step 1: 实现 routes/api.py
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

### Step 2: 运行应用验证路由
```bash
uv run uvicorn main:app --reload
```
访问 `http://localhost:8000/docs` 应该能看到 API 文档

### Step 3: 提交代码
```bash
git add routes/
git commit -m "feat: API 路由"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
