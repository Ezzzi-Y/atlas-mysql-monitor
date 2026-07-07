# models/metrics.py
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


async def save_metrics(db_path: str, metrics: Dict[str, Any]) -> None:
    """保存一条指标记录"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO mysql_metrics (
                threads_connected, threads_running, uptime, slow_queries,
                com_select, com_insert, com_update, com_delete,
                select_qps, insert_qps, update_qps, delete_qps
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics["threads_connected"],
            metrics["threads_running"],
            metrics["uptime"],
            metrics["slow_queries"],
            metrics["com_select"],
            metrics["com_insert"],
            metrics["com_update"],
            metrics["com_delete"],
            metrics["select_qps"],
            metrics["insert_qps"],
            metrics["update_qps"],
            metrics["delete_qps"],
        ))
        await db.commit()


async def get_latest_metrics(db_path: str) -> Optional[Dict[str, Any]]:
    """获取最新一条指标"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM mysql_metrics ORDER BY id DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_metrics_history(db_path: str, hours: int = 24) -> List[Dict[str, Any]]:
    """获取最近 N 小时的指标历史"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        since = datetime.now() - timedelta(hours=hours)
        cursor = await db.execute(
            "SELECT * FROM mysql_metrics WHERE timestamp >= ? ORDER BY timestamp",
            (since.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def cleanup_old_metrics(db_path: str, retention_days: int = 30) -> int:
    """清理超过保留天数的旧数据，返回删除的行数"""
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        cutoff = datetime.now() - timedelta(days=retention_days)
        cursor = await db.execute(
            "DELETE FROM mysql_metrics WHERE timestamp < ?",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        await db.commit()
        return cursor.rowcount
