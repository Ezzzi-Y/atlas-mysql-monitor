# main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import config
from database import init_db, DEFAULT_DB_PATH
from models.metrics import save_metrics, get_latest_metrics, cleanup_old_metrics
from collectors.mysql_collector import MySQLCollector
from routes import dashboard, api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局状态
collector: MySQLCollector = None
collect_task: asyncio.Task = None
consecutive_failures: int = 0
last_success_time: str = None


async def collect_loop():
    """后台采集循环"""
    global consecutive_failures, last_success_time

    previous_metrics = None

    while True:
        try:
            # 采集当前指标
            current_metrics = await collector.collect()

            # 计算 QPS
            if previous_metrics:
                qps = collector._calculate_qps(
                    current_metrics,
                    previous_metrics,
                    config.COLLECT_INTERVAL
                )
                current_metrics.update(qps)
            else:
                # 首次采集，QPS 为 None
                current_metrics.update({
                    "select_qps": None,
                    "insert_qps": None,
                    "update_qps": None,
                    "delete_qps": None,
                })

            # 保存到数据库
            await save_metrics(str(DEFAULT_DB_PATH), current_metrics)

            # 更新状态
            previous_metrics = current_metrics
            consecutive_failures = 0
            last_success_time = current_metrics.get("timestamp")

            logger.info("指标采集成功")

        except Exception as e:
            consecutive_failures += 1
            logger.error(f"采集失败（连续失败 {consecutive_failures} 次）: {e}")

        await asyncio.sleep(config.COLLECT_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global collector, collect_task

    # 启动时初始化
    logger.info("正在初始化数据库...")
    await init_db()

    # 清理过期数据
    deleted = await cleanup_old_metrics(str(DEFAULT_DB_PATH), config.RETENTION_DAYS)
    if deleted > 0:
        logger.info(f"已清理 {deleted} 条过期数据")

    # 创建采集器
    logger.info("正在连接 MySQL...")
    collector = MySQLCollector(config)

    # 启动后台采集任务
    logger.info(f"启动后台采集任务（间隔 {config.COLLECT_INTERVAL} 秒）...")
    collect_task = asyncio.create_task(collect_loop())

    yield

    # 关闭时清理
    if collect_task:
        collect_task.cancel()
        try:
            await collect_task
        except asyncio.CancelledError:
            pass

    if collector:
        await collector.close()

    logger.info("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(title="Atlas MySQL Monitor", lifespan=lifespan)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(dashboard.router)
app.include_router(api.router)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
