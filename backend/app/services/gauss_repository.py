# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
openGauss 事件仓库，使用 py-opengauss 原生 PG-API。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.db.opengauss_connection import get_connection
from app.services.query import EventQuery
from app.services.stats import iter_buckets
from app.utils.errors import DatabaseError
from app.utils.timeutil import to_iso

__all__ = ["GaussRepository"]

_TABLE = "cli_command_event"
_DIM_COLUMNS = {
    "result": "result",
    "domain": "domain",
    "platform": "platform",
    "environment": "environment",
    "input_source": "input_source",
    "cli_version": "cli_version",
    "output_format": "output_format",
    "command_name": "command_name",
    "error_category": "error_category",
    "error_code": "error_code",
}
_DEPARTMENT_COLUMNS = {
    "org_dept_name4": "org_dept_name4",
    "org_dept_name5": "org_dept_name5",
    "org_dept_name6": "org_dept_name6",
}
_FILTER_COLUMNS = {
    "domains": "domain",
    "platforms": "platform",
    "environments": "environment",
    "results": "result",
    "command_names": "command_name",
    "input_sources": "input_source",
    "cli_versions": "cli_version",
}
_EVENT_COLUMNS = (
    "id",
    "event_id",
    "event_time",
    "cli_version",
    "domain",
    "platform",
    "command",
    "command_name",
    "duration_ms",
    "api_duration_ms",
    "api_calls",
    "input_source",
    "output_format",
    "result",
    "exit_code",
    "environment",
    "error_category",
    "error_code",
    "args_detail",
    "user_id",
    "user_cn_name",
    "user_long_id",
    "org_dept_code4",
    "org_dept_name4",
    "org_dept_code5",
    "org_dept_name5",
    "org_dept_code6",
    "org_dept_name6",
)
_METRIC_SQL = """
    COUNT(*) AS total_calls,
    COUNT(DISTINCT user_id) AS unique_users,
    COALESCE(SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END), 0) AS success_count,
    COALESCE(SUM(CASE WHEN result = 'failure' THEN 1 ELSE 0 END), 0) AS failure_count,
    COALESCE(AVG(duration_ms), 0) AS avg_duration_ms,
    COALESCE(AVG(api_duration_ms), 0) AS avg_api_duration_ms
"""


def _num(value: Any, default: float = 0.0) -> float:
    return default if value is None else float(value)


def _value(row: Any, key: str, index: Optional[int] = None) -> Any:
    try:
        return row[key]
    except (KeyError, TypeError):
        if hasattr(row, key):
            return getattr(row, key)
        if index is not None:
            return row[index]
        raise


def _where(
    query: EventQuery,
    *,
    ignore_dimension: bool = False,
    ignore_time: bool = False,
    parameter_offset: int = 0,
) -> Tuple[str, List[Any]]:
    conditions: List[str] = []
    params: List[Any] = []

    def add(condition: str, value: Any) -> None:
        params.append(value)
        conditions.append(condition.format(index=parameter_offset + len(params)))

    if not ignore_time:
        add("event_time >= ${index}", query.start)
        add("event_time < ${index}", query.end)
    if not ignore_dimension:
        for column, value in (
            ("domain", query.domain),
            ("platform", query.platform),
            ("environment", query.environment),
            ("result", query.result),
            ("command_name", query.command_name),
            ("user_id", query.user_id),
            ("input_source", query.input_source),
        ):
            if value:
                add(f"{column} = ${{index}}", value)
        if query.keyword:
            params.append(f"%{query.keyword}%")
            placeholder = f"${parameter_offset + len(params)}"
            conditions.append(
                "("
                + " OR ".join(
                    f"{column} ILIKE {placeholder}"
                    for column in ("command", "command_name", "event_id", "user_id", "user_cn_name")
                )
                + ")"
            )
    return " AND ".join(conditions) or "TRUE", params


class GaussRepository:
    source = "gaussdb"

    def _rows(self, sql: str, params: Sequence[Any] = ()) -> List[Any]:
        try:
            return list(get_connection().prepare(sql)(*params))
        except Exception as exc:
            raise DatabaseError("Failed to query command events") from exc

    def _one(self, sql: str, params: Sequence[Any] = ()) -> Any:
        rows = self._rows(sql, params)
        if not rows:
            raise DatabaseError("Database query returned no rows")
        return rows[0]

    def _row_metrics(self, row: Any) -> Dict[str, Any]:
        total = int(_num(_value(row, "total_calls")))
        success_count = int(_num(_value(row, "success_count")))
        return {
            "total_calls": total,
            "unique_users": int(_num(_value(row, "unique_users"))),
            "success_count": success_count,
            "failure_count": int(_num(_value(row, "failure_count"))),
            "success_rate": (success_count / total * 100) if total else 0,
            "avg_duration_ms": _num(_value(row, "avg_duration_ms")),
            "avg_api_duration_ms": _num(_value(row, "avg_api_duration_ms")),
        }

    def earliest_time(self, query: EventQuery) -> Optional[datetime]:
        where, params = _where(query, ignore_time=True)
        row = self._one(f"SELECT MIN(event_time) AS earliest FROM {_TABLE} WHERE {where}", params)
        return _value(row, "earliest", 0)

    def metrics(self, query: EventQuery) -> Dict[str, Any]:
        where, params = _where(query)
        row = self._one(f"SELECT {_METRIC_SQL} FROM {_TABLE} WHERE {where}", params)
        return self._row_metrics(row)

    def new_users(self, query: EventQuery) -> int:
        where, dimension_params = _where(query, ignore_time=True, parameter_offset=2)
        sql = f"""
            SELECT COUNT(*) AS new_users
            FROM (
                SELECT user_id, MIN(event_time) AS first_seen
                FROM {_TABLE}
                WHERE {where}
                GROUP BY user_id
            ) first_seen_users
            WHERE first_seen >= $1 AND first_seen < $2
        """
        row = self._one(sql, [query.start, query.end, *dimension_params])
        return int(_num(_value(row, "new_users", 0)))

    def trend(self, query: EventQuery) -> List[Dict[str, Any]]:
        where, where_params = _where(query, parameter_offset=1)
        sql = f"""
            SELECT date_trunc($1::text, event_time) AS bucket, {_METRIC_SQL}
            FROM {_TABLE}
            WHERE {where}
            GROUP BY bucket
            ORDER BY bucket
        """
        fetched = {
            _value(row, "bucket"): self._row_metrics(row)
            for row in self._rows(sql, [query.granularity, *where_params])
        }
        rows = []
        for start in iter_buckets(query.start, query.end, query.granularity):
            metrics = fetched.get(start) or fetched.get(start.replace(tzinfo=None))
            metrics = metrics or {
                "total_calls": 0,
                "unique_users": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0,
                "avg_duration_ms": 0,
                "avg_api_duration_ms": 0,
            }
            rows.append(
                {
                    "bucket": start.isoformat(),
                    "calls": metrics["total_calls"],
                    "users": metrics["unique_users"],
                    "success_rate": metrics["success_rate"],
                    "avg_duration_ms": metrics["avg_duration_ms"],
                    "avg_api_duration_ms": metrics["avg_api_duration_ms"],
                }
            )
        return rows

    def distribution(self, query: EventQuery, key: str, limit: int = 20) -> List[Dict[str, Any]]:
        column = _DIM_COLUMNS[key]
        where, params = _where(query)
        limit_placeholder = f"${len(params) + 1}"
        sql = f"""
            SELECT COALESCE({column}, 'unknown') AS name, {_METRIC_SQL}
            FROM {_TABLE}
            WHERE {where}
            GROUP BY COALESCE({column}, 'unknown')
            ORDER BY total_calls DESC
            LIMIT {limit_placeholder}
        """
        return [
            {"name": _value(row, "name"), **self._row_metrics(row)}
            for row in self._rows(sql, [*params, limit])
        ]

    def commands(self, query: EventQuery, limit: int = 30) -> List[Dict[str, Any]]:
        where, params = _where(query)
        sql = f"""
            SELECT domain, platform, command, command_name, {_METRIC_SQL}
            FROM {_TABLE}
            WHERE {where}
            GROUP BY domain, platform, command, command_name
            ORDER BY total_calls DESC
            LIMIT ${len(params) + 1}
        """
        return [
            {
                "domain": _value(row, "domain"),
                "platform": _value(row, "platform"),
                "command": _value(row, "command"),
                "command_name": _value(row, "command_name"),
                **self._row_metrics(row),
            }
            for row in self._rows(sql, [*params, limit])
        ]

    def users(self, query: EventQuery, limit: int = 30) -> List[Dict[str, Any]]:
        where, params = _where(query)
        sql = f"""
            SELECT user_id,
                   MAX(user_cn_name) AS user_cn_name,
                   MAX(org_dept_name4) AS org_dept_name4,
                   MAX(org_dept_name5) AS org_dept_name5,
                   MAX(event_time) AS last_seen,
                   {_METRIC_SQL}
            FROM {_TABLE}
            WHERE {where}
            GROUP BY user_id
            ORDER BY total_calls DESC
            LIMIT ${len(params) + 1}
        """
        return [
            {
                "user_id": _value(row, "user_id"),
                "user_cn_name": _value(row, "user_cn_name"),
                "org_dept_name4": _value(row, "org_dept_name4"),
                "org_dept_name5": _value(row, "org_dept_name5"),
                "last_seen": to_iso(_value(row, "last_seen")),
                **self._row_metrics(row),
            }
            for row in self._rows(sql, [*params, limit])
        ]

    def departments(
        self,
        query: EventQuery,
        field: str = "org_dept_name4",
        dept4: Optional[str] = None,
        dept5: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        column = _DEPARTMENT_COLUMNS.get(field, "org_dept_name4")
        where, params = _where(query)
        conditions = [where]
        if dept4:
            params.append(dept4)
            conditions.append(f"org_dept_name4 = ${len(params)}")
        if dept5:
            params.append(dept5)
            conditions.append(f"org_dept_name5 = ${len(params)}")
        sql = f"""
            SELECT COALESCE({column}, '未填写部门') AS name, {_METRIC_SQL}
            FROM {_TABLE}
            WHERE {" AND ".join(conditions)}
            GROUP BY COALESCE({column}, '未填写部门')
            ORDER BY total_calls DESC
        """
        return [
            {"name": _value(row, "name"), **self._row_metrics(row)}
            for row in self._rows(sql, params)
        ]

    def error_categories(self, query: EventQuery) -> List[Dict[str, Any]]:
        return self._error_group(query, "error_category")

    def error_codes(self, query: EventQuery, limit: int = 15) -> List[Dict[str, Any]]:
        return self._error_group(query, "error_code", limit=limit)

    def _error_group(
        self,
        query: EventQuery,
        key: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        column = _DIM_COLUMNS[key]
        where, params = _where(query)
        limit_sql = ""
        if limit is not None:
            params.append(limit)
            limit_sql = f"LIMIT ${len(params)}"
        sql = f"""
            SELECT COALESCE({column}, 'unknown') AS name, {_METRIC_SQL}
            FROM {_TABLE}
            WHERE {where} AND {column} IS NOT NULL
            GROUP BY COALESCE({column}, 'unknown')
            ORDER BY total_calls DESC
            {limit_sql}
        """
        return [
            {"name": _value(row, "name"), **self._row_metrics(row)}
            for row in self._rows(sql, params)
        ]

    def duration_histogram(self, query: EventQuery) -> List[Dict[str, Any]]:
        labels = ("<200ms", "200-500ms", "500ms-1s", "1-2s", "2-5s", "5-10s", "10-30s", ">=30s")
        where, params = _where(query)
        sql = f"""
            SELECT
                COALESCE(SUM(CASE WHEN duration_ms < 200 THEN 1 ELSE 0 END), 0) AS b0,
                COALESCE(SUM(CASE WHEN duration_ms >= 200 AND duration_ms < 500 THEN 1 ELSE 0 END), 0) AS b1,
                COALESCE(SUM(CASE WHEN duration_ms >= 500 AND duration_ms < 1000 THEN 1 ELSE 0 END), 0) AS b2,
                COALESCE(SUM(CASE WHEN duration_ms >= 1000 AND duration_ms < 2000 THEN 1 ELSE 0 END), 0) AS b3,
                COALESCE(SUM(CASE WHEN duration_ms >= 2000 AND duration_ms < 5000 THEN 1 ELSE 0 END), 0) AS b4,
                COALESCE(SUM(CASE WHEN duration_ms >= 5000 AND duration_ms < 10000 THEN 1 ELSE 0 END), 0) AS b5,
                COALESCE(SUM(CASE WHEN duration_ms >= 10000 AND duration_ms < 30000 THEN 1 ELSE 0 END), 0) AS b6,
                COALESCE(SUM(CASE WHEN duration_ms >= 30000 THEN 1 ELSE 0 END), 0) AS b7
            FROM {_TABLE}
            WHERE {where}
        """
        row = self._one(sql, params)
        return [
            {"name": label, "total_calls": int(_num(_value(row, f"b{index}", index)))}
            for index, label in enumerate(labels)
        ]

    def filter_options(self, query: EventQuery) -> Dict[str, List[str]]:
        where, params = _where(query, ignore_dimension=True)
        result: Dict[str, List[str]] = {}
        for name, column in _FILTER_COLUMNS.items():
            sql = f"""
                SELECT DISTINCT {column} AS value
                FROM {_TABLE}
                WHERE {where} AND {column} IS NOT NULL
                ORDER BY {column}
            """
            result[name] = [
                value
                for row in self._rows(sql, params)
                if (value := _value(row, "value", 0))
            ]
        return result

    def events(self, query: EventQuery, limit: int, offset: int) -> Tuple[List[Dict[str, Any]], int]:
        where, params = _where(query)
        total_row = self._one(
            f"SELECT COUNT(*) AS total FROM {_TABLE} WHERE {where}",
            params,
        )
        sql = f"""
            SELECT {", ".join(_EVENT_COLUMNS)}
            FROM {_TABLE}
            WHERE {where}
            ORDER BY event_time DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        rows = self._rows(sql, [*params, limit, offset])
        return [_serialize_row(row) for row in rows], int(_num(_value(total_row, "total", 0)))


def _serialize_row(row: Any) -> Dict[str, Any]:
    payload = {
        column: _value(row, column, index)
        for index, column in enumerate(_EVENT_COLUMNS)
    }
    payload["event_time"] = to_iso(payload["event_time"])
    return payload
