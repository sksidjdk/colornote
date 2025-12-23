import os

from flask import Flask

from .config import load_config
from .db import init_db
from .routes import register_routes


def create_app() -> Flask:
    """
    Flask application factory.
    读取环境变量配置 TiDB 连接，并初始化数据库与路由。
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # 加载配置（从 .env / 环境变量）
    load_config(app)

    # 初始化数据库（创建表等）
    init_db(app)

    # 注册前端页面和 API 路由
    register_routes(app)

    return app


# 供本地调试（python -m flask --app app run）或 vercel python 入口使用
app = create_app()


