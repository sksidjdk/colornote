from __future__ import annotations

from typing import Generator

from flask import Flask, current_app, g
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


SessionLocal: sessionmaker[Session] | None = None


def init_db(app: Flask) -> None:
    """
    根据应用配置初始化 SQLAlchemy 引擎与会话工厂，并创建所有模型表。
    """
    global SessionLocal

    database_url = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not database_url:
        # 允许先启动应用，但后续访问数据库时会报错，方便你先调通前端
        app.logger.warning("SQLALCHEMY_DATABASE_URI 未配置，数据库相关功能将不可用")
        return

    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # 推迟导入，避免循环引用
    from .models import Note  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # 将 session factory 挂到 app 上，方便在其他地方使用
    app.extensions["sqlalchemy_session_factory"] = SessionLocal


def get_db_session() -> Session:
    """
    在 Flask 请求上下文中获取一个 Session，自动管理生命周期。
    """
    if "db_session" not in g:
        session_factory: sessionmaker[Session] | None = current_app.extensions.get(
            "sqlalchemy_session_factory"
        )
        if session_factory is None:
            raise RuntimeError("数据库尚未初始化，请检查 SQLALCHEMY_DATABASE_URI 配置")
        g.db_session = session_factory()
    return g.db_session  # type: ignore[no-any-return]


def close_db_session(e: Exception | None = None) -> None:  # noqa: ARG001
    """
    在请求结束时关闭 Session。
    """
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


