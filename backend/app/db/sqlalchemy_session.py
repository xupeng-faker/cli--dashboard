# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
SQLAlchemy engine 与 session 管理（GaussDB / OpenGauss）。
"""
import logging
from contextlib import contextmanager
from urllib.parse import quote_plus

from flask import current_app
from sqlalchemy import create_engine, text
from sqlalchemy.dialects import registry
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

__all__ = ["init_sqlalchemy_engine", "get_session", "close_engine", "get_engine"]

_engine = None
_session_factory = None

registry.register(
    "gaussdb.gaussdb",
    "app.db.gaussdb_dialect",
    "GaussDBDialect",
)


def init_sqlalchemy_engine(app) -> None:
    """
    初始化 SQLAlchemy engine 和 session factory。
    """
    global _engine, _session_factory
    schema = app.config.get("GAUSS_SCHEMA", "coreinfactory")
    sslmode = app.config.get("GAUSS_SSLMODE", "disable")
    db_url = _build_gauss_url(
        host=app.config["GAUSS_HOST"],
        port=app.config["GAUSS_PORT"],
        user=app.config["GAUSS_USER"],
        password=app.config["GAUSS_PASSWORD"],
        database=app.config["GAUSS_DATABASE"],
        sslmode=sslmode,
    )

    connect_args = {
        "options": f"-csearch_path={schema},public -ctimezone=Asia/Shanghai",
    }

    _engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
        connect_args=connect_args,
    )
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)

    logger.info(
        "GaussDB engine initialized. Host '%s:%s', User '%s', Database '%s', Schema '%s'",
        app.config["GAUSS_HOST"],
        app.config["GAUSS_PORT"],
        app.config["GAUSS_USER"],
        app.config["GAUSS_DATABASE"],
        schema,
    )


def _build_gauss_url(host: str, port: int, user: str, password: str, database: str, sslmode: str) -> str:
    encoded_user = quote_plus(user)
    encoded_password = quote_plus(password)
    return (
        f"gaussdb+gaussdb://{encoded_user}:{encoded_password}@{host}:{port}/{database}"
        f"?sslmode={sslmode}"
    )


@contextmanager
def get_session() -> Session:
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call init_sqlalchemy_engine() first.")

    session = _session_factory()
    try:
        yield session
    except SQLAlchemyError as exc:
        logger.exception("Database session error occurred: %s", str(exc))
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()


def close_engine() -> None:
    global _engine, _session_factory
    if _engine is None:
        return
    try:
        _engine.dispose()
    finally:
        _engine = None
        _session_factory = None


def get_engine():
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_sqlalchemy_engine() first.")
    return _engine


def ping_database() -> bool:
    if _engine is None:
        return False
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.exception("GaussDB ping failed")
        return False
