# database.py
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

# 确保 data 目录存在
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_DB_PATH = DATA_DIR / "monitor.db"


async def init_db(db_path: str = None):
    """初始化数据库，创建表结构"""
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mysql_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
                threads_connected INTEGER,
                threads_running INTEGER,
                uptime INTEGER,
                slow_queries INTEGER,
                com_select INTEGER,
                com_insert INTEGER,
                com_update INTEGER,
                com_delete INTEGER,
                select_qps REAL,
                insert_qps REAL,
                update_qps REAL,
                delete_qps REAL
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON mysql_metrics(timestamp)"
        )
        await db.commit()


@asynccontextmanager
async def get_db(db_path: str = None):
    """获取数据库连接的上下文管理器"""
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    db = await aiosqlite.connect(db_path)
    try:
        yield db
    finally:
        await db.close()
