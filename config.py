from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # MySQL 连接配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "mysql"

    # 监控配置
    COLLECT_INTERVAL: int = 60  # 采集间隔（秒）
    RETENTION_DAYS: int = 30    # 数据保留天数

    model_config = {"env_file": ".env"}


config = Config()
