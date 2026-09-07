# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
SQLAlchemy 方言适配：使用 GaussDB 官方 Python DBAPI 驱动。
"""
import os
import re
from typing import Any, Tuple

from sqlalchemy.dialects.postgresql.base import PGDialect

__all__ = ["GaussDBDialect"]


class GaussDBDialect(PGDialect):
    """复用 PostgreSQL SQL 编译能力，并将连接交给 gaussdb-python。"""

    name = "gaussdb"
    driver = "gaussdb"
    supports_statement_cache = True
    default_paramstyle = "pyformat"

    @classmethod
    def import_dbapi(cls):
        os.environ.setdefault("PSYCOPG_IMPL", "python")
        try:
            import gaussdb
        except ImportError as exc:
            raise ImportError(
                "GaussDB Python 驱动加载失败。请安装 gaussdb，并确保官方 GaussDB "
                "客户端 libpq 动态库已加入 PATH（Windows）或 LD_LIBRARY_PATH（Linux）。"
            ) from exc
        return gaussdb

    def create_connect_args(self, url) -> Tuple[list, dict]:
        options = url.translate_connect_args(username="user", database="dbname")
        options.update(url.query)
        return [], options

    def is_disconnect(self, error: Exception, connection: Any, cursor: Any) -> bool:
        if not isinstance(error, self.dbapi.Error):
            return False
        if connection is None:
            return True
        return bool(getattr(connection, "closed", False) or getattr(connection, "broken", False))

    def _get_server_version_info(self, connection) -> Tuple[int, ...]:
        value = str(connection.exec_driver_sql("SELECT version()").scalar() or "")
        match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", value)
        if not match:
            return (9, 2)
        return tuple(int(part) for part in match.groups() if part is not None)
