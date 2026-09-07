# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
py-opengauss PG-API 连接管理。
"""
import logging
from urllib.parse import quote, urlencode

import py_opengauss
from flask import current_app, g

logger = logging.getLogger(__name__)

__all__ = ["init_database", "get_connection", "close_connection", "ping_database"]

_CONNECTION_KEY = "_opengauss_connection"


def _build_connection_url() -> str:
    user = quote(str(current_app.config["GAUSS_USER"]), safe="")
    password = quote(str(current_app.config["GAUSS_PASSWORD"]), safe="")
    host = str(current_app.config["GAUSS_HOST"])
    port = int(current_app.config["GAUSS_PORT"])
    database = quote(str(current_app.config["GAUSS_DATABASE"]), safe="")
    sslmode = str(current_app.config.get("GAUSS_SSLMODE", "disable"))
    query = urlencode({"[sslmode]": sslmode})
    return f"opengauss://{user}:{password}@{host}:{port}/{database}?{query}"


def get_connection():
    """获取当前 Flask 请求/应用上下文复用的数据库连接。"""
    connection = g.get(_CONNECTION_KEY)
    if connection is not None:
        return connection

    connection = py_opengauss.open(_build_connection_url())
    try:
        schema = str(current_app.config.get("GAUSS_SCHEMA", "coreinfactory"))
        connection.settings.update(
            {
                "search_path": f"{schema},public",
                "timezone": "Asia/Shanghai",
            }
        )
    except Exception:
        connection.close()
        raise

    setattr(g, _CONNECTION_KEY, connection)
    logger.debug("Opened an openGauss connection for the current request")
    return connection


def close_connection(_error=None) -> None:
    """关闭当前 Flask 上下文持有的数据库连接。"""
    connection = g.pop(_CONNECTION_KEY, None)
    if connection is not None:
        connection.close()
        logger.debug("Closed the openGauss connection for the current request")


def ping_database() -> bool:
    """使用当前请求连接执行轻量数据库探活。"""
    try:
        get_connection().prepare("SELECT 1 AS ok")()
        return True
    except Exception:
        logger.exception("openGauss ping failed")
        return False


def init_database(app) -> None:
    """注册 Flask 应用上下文结束时的连接清理。"""
    app.teardown_appcontext(close_connection)
