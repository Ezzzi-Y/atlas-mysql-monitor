# collectors/mysql_collector.py
import aiomysql
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MySQLCollector:
    """MySQL 指标采集器"""

    def __init__(self, config):
        self.config = config
        self.pool: Optional[aiomysql.Pool] = None

    async def connect(self):
        """创建连接池"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                db=self.config.MYSQL_DATABASE,
                minsize=1,
                maxsize=2,
            )
            logger.info("MySQL 连接池创建成功")
        except Exception as e:
            logger.error(f"MySQL 连接失败: {e}")
            raise

    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def collect(self) -> Dict[str, Any]:
        """采集 MySQL 指标"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW GLOBAL STATUS")
                rows = await cursor.fetchall()
                status_data = {row[0]: row[1] for row in rows}

        metrics = self._parse_status(status_data)
        return metrics

    def _parse_status(self, status_data: Dict[str, str]) -> Dict[str, Any]:
        """解析 MySQL 状态数据"""
        return {
            "threads_connected": int(status_data.get("Threads_connected", 0)),
            "threads_running": int(status_data.get("Threads_running", 0)),
            "uptime": int(status_data.get("Uptime", 0)),
            "slow_queries": int(status_data.get("Slow_queries", 0)),
            "com_select": int(status_data.get("Com_select", 0)),
            "com_insert": int(status_data.get("Com_insert", 0)),
            "com_update": int(status_data.get("Com_update", 0)),
            "com_delete": int(status_data.get("Com_delete", 0)),
        }

    def _calculate_qps(
        self, current: Dict[str, int], previous: Dict[str, int], interval: int
    ) -> Dict[str, float]:
        """计算各类 QPS"""
        return {
            "select_qps": (current["com_select"] - previous["com_select"]) / interval,
            "insert_qps": (current["com_insert"] - previous["com_insert"]) / interval,
            "update_qps": (current["com_update"] - previous["com_update"]) / interval,
            "delete_qps": (current["com_delete"] - previous["com_delete"]) / interval,
        }
