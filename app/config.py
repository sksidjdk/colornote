import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask


def load_config(app: Flask) -> None:
    """
    从 .env 与系统环境变量加载配置，并配置 SQLAlchemy 连接串。
    """
    # 尝试从项目根目录加载 .env
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    app.config["APP_ENV"] = os.getenv("APP_ENV", "local")
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")

    db_host = os.getenv("DB_HOST", "")
    db_port = os.getenv("DB_PORT", "4000")
    db_user = os.getenv("DB_USERNAME", "")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_DATABASE", "")

    # TiDB/MySQL 连接 URL（SQLAlchemy）
    if db_host and db_user and db_name:
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        # 占位，防止后续使用时报错太难理解
        app.config["SQLALCHEMY_DATABASE_URI"] = ""

    app.config["SQLALCHEMY_ECHO"] = False


