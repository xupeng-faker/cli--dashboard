# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
GaussDB 事件仓库。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.sqlalchemy_session import get_session
from app.models.cli_event import CliCommandEvent
from app.services.query import EventQuery
from app.services.stats import iter_buckets
from app.utils.errors import DatabaseError
from app.utils.timeutil import to_iso

__all__ = ["GaussRepository"]

Event = CliCommandEvent


def _num(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _success_case():
    return case((Event.result == "success", 1), else_=0)


def _failure_case():
    return case((Event.result == "failure", 1), else_=0)


_DIM_COLUMNS = {
    "result": Event.result,
    "domain": Event.domain,
    "platform": Event.platform,
    "environment": Event.environment,
    "input_source": Event.input_source,
    "cli_version": Event.cli_version,
    "output_format": Event.output_format,
    "command_name": Event.command_name,
    "error_category": Event.error_category,
    "error_code": Event.error_code,
}


class GaussRepository:
    source = "gaussdb"

    def _where(self, query: EventQuery, *, ignore_dimension: bool = False, ignore_time: bool = False):
        conds = []
        if not ignore_time:
            conds.extend(
                [
                    Event.event_time >= query.start,
                    Event.event_time < query.end,
                ]
            )
        if ignore_dimension:
            return conds
        if query.domain:
            conds.append(Event.domain == query.domain)
        if query.platform:
            conds.append(Event.platform == query.platform)
        if query.environment:
            conds.append(Event.environment == query.environment)
        if query.result:
            conds.append(Event.result == query.result)
        if query.command_name:
            conds.append(Event.command_name == query.command_name)
        if query.user_id:
            conds.append(Event.user_id == query.user_id)
        if query.input_source:
            conds.append(Event.input_source == query.input_source)
        if query.keyword:
            like = f"%{query.keyword}%"
            conds.append(
                or_(
                    Event.command.ilike(like),
                    Event.command_name.ilike(like),
                    Event.event_id.ilike(like),
                    Event.user_id.ilike(like),
                    Event.user_cn_name.ilike(like),
                )
            )
        return conds

    def _execute(self, handler):
        try:
            with get_session() as session:
                return handler(session)
        except SQLAlchemyError as exc:
            raise DatabaseError("Failed to query command events") from exc

    def _metric_columns(self):
        return [
            func.count().label("total_calls"),
            func.count(func.distinct(Event.user_id)).label("unique_users"),
            func.coalesce(func.sum(_success_case()), 0).label("success_count"),
            func.coalesce(func.sum(_failure_case()), 0).label("failure_count"),
            func.coalesce(func.avg(Event.duration_ms), 0).label("avg_duration_ms"),
            func.coalesce(func.avg(Event.api_duration_ms), 0).label("avg_api_duration_ms"),
        ]

    def _row_metrics(self, row: Any) -> Dict[str, Any]:
        total = int(_num(row.total_calls))
        success_count = int(_num(row.success_count))
        return {
            "total_calls": total,
            "unique_users": int(_num(getattr(row, "unique_users", 0))),
            "success_count": success_count,
            "failure_count": int(_num(row.failure_count)),
            "success_rate": (success_count / total * 100) if total else 0,
            "avg_duration_ms": _num(row.avg_duration_ms),
            "avg_api_duration_ms": _num(getattr(row, "avg_api_duration_ms", 0)),
        }

    def earliest_time(self, query: EventQuery) -> Optional[datetime]:
        def handler(session: Session) -> Optional[datetime]:
            stmt = select(func.min(Event.event_time)).where(*self._where(query, ignore_time=True))
            return session.execute(stmt).scalar()

        return self._execute(handler)

    def metrics(self, query: EventQuery) -> Dict[str, Any]:
        def handler(session: Session) -> Dict[str, Any]:
            stmt = select(*self._metric_columns()).where(*self._where(query))
            row = session.execute(stmt).one()
            return self._row_metrics(row)

        return self._execute(handler)

    def new_users(self, query: EventQuery) -> int:
        def handler(session: Session) -> int:
            first_seen = (
                select(
                    Event.user_id.label("user_id"),
                    func.min(Event.event_time).label("first_seen"),
                )
                .where(*self._where(query, ignore_time=True))
                .group_by(Event.user_id)
                .subquery()
            )
            stmt = select(func.count()).select_from(first_seen).where(
                first_seen.c.first_seen >= query.start,
                first_seen.c.first_seen < query.end,
            )
            return int(session.execute(stmt).scalar_one())

        return self._execute(handler)

    def trend(self, query: EventQuery) -> List[Dict[str, Any]]:
        def handler(session: Session) -> List[Dict[str, Any]]:
            bucket = func.date_trunc(query.granularity, Event.event_time)
            stmt = (
                select(bucket.label("bucket"), *self._metric_columns())
                .where(*self._where(query))
                .group_by(bucket)
                .order_by(bucket)
            )
            fetched = {row.bucket: self._row_metrics(row) for row in session.execute(stmt)}
            rows = []
            for start in iter_buckets(query.start, query.end, query.granularity):
                metrics = fetched.get(start) or fetched.get(start.replace(tzinfo=None))
                if metrics is None:
                    metrics = self._row_metrics(
                        type("Empty", (), {
                            "total_calls": 0,
                            "unique_users": 0,
                            "success_count": 0,
                            "failure_count": 0,
                            "avg_duration_ms": 0,
                            "avg_api_duration_ms": 0,
                        })()
                    )
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

        return self._execute(handler)

    def distribution(self, query: EventQuery, key: str, limit: int = 20) -> List[Dict[str, Any]]:
        column = _DIM_COLUMNS[key]
        dim = func.coalesce(column, "unknown")

        def handler(session: Session) -> List[Dict[str, Any]]:
            stmt = (
                select(dim.label("name"), *self._metric_columns())
                .where(*self._where(query))
                .group_by(dim)
                .order_by(func.count().desc())
                .limit(limit)
            )
            return [{"name": row.name, **self._row_metrics(row)} for row in session.execute(stmt)]

        return self._execute(handler)

    def commands(self, query: EventQuery, limit: int = 30) -> List[Dict[str, Any]]:
        def handler(session: Session) -> List[Dict[str, Any]]:
            stmt = (
                select(
                    Event.domain,
                    Event.platform,
                    Event.command,
                    Event.command_name,
                    *self._metric_columns(),
                )
                .where(*self._where(query))
                .group_by(Event.domain, Event.platform, Event.command, Event.command_name)
                .order_by(func.count().desc())
                .limit(limit)
            )
            return [
                {
                    "domain": row.domain,
                    "platform": row.platform,
                    "command": row.command,
                    "command_name": row.command_name,
                    **self._row_metrics(row),
                }
                for row in session.execute(stmt)
            ]

        return self._execute(handler)

    def users(self, query: EventQuery, limit: int = 30) -> List[Dict[str, Any]]:
        def handler(session: Session) -> List[Dict[str, Any]]:
            stmt = (
                select(
                    Event.user_id,
                    func.max(Event.user_cn_name).label("user_cn_name"),
                    func.max(Event.org_dept_name4).label("org_dept_name4"),
                    func.max(Event.org_dept_name5).label("org_dept_name5"),
                    func.max(Event.event_time).label("last_seen"),
                    *self._metric_columns(),
                )
                .where(*self._where(query))
                .group_by(Event.user_id)
                .order_by(func.count().desc())
                .limit(limit)
            )
            return [
                {
                    "user_id": row.user_id,
                    "user_cn_name": row.user_cn_name,
                    "org_dept_name4": row.org_dept_name4,
                    "org_dept_name5": row.org_dept_name5,
                    "last_seen": to_iso(row.last_seen),
                    **self._row_metrics(row),
                }
                for row in session.execute(stmt)
            ]

        return self._execute(handler)

    def departments(
        self,
        query: EventQuery,
        field: str = "org_dept_name4",
        dept4: Optional[str] = None,
        dept5: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        columns = {
            "org_dept_name4": Event.org_dept_name4,
            "org_dept_name5": Event.org_dept_name5,
            "org_dept_name6": Event.org_dept_name6,
        }
        column = columns.get(field, Event.org_dept_name4)
        dim = func.coalesce(column, "未填写部门")

        def handler(session: Session) -> List[Dict[str, Any]]:
            conditions = self._where(query)
            if dept4:
                conditions.append(Event.org_dept_name4 == dept4)
            if dept5:
                conditions.append(Event.org_dept_name5 == dept5)
            stmt = (
                select(dim.label("name"), *self._metric_columns())
                .where(*conditions)
                .group_by(dim)
                .order_by(func.count().desc())
            )
            return [{"name": row.name, **self._row_metrics(row)} for row in session.execute(stmt)]

        return self._execute(handler)

    def error_categories(self, query: EventQuery) -> List[Dict[str, Any]]:
        return self._error_group(query, Event.error_category)

    def error_codes(self, query: EventQuery, limit: int = 15) -> List[Dict[str, Any]]:
        return self._error_group(query, Event.error_code, limit=limit)

    def _error_group(self, query: EventQuery, column, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        dim = func.coalesce(column, "unknown")

        def handler(session: Session) -> List[Dict[str, Any]]:
            stmt = (
                select(dim.label("name"), *self._metric_columns())
                .where(*self._where(query), column.is_not(None))
                .group_by(dim)
                .order_by(func.count().desc())
            )
            if limit is not None:
                stmt = stmt.limit(limit)
            return [{"name": row.name, **self._row_metrics(row)} for row in session.execute(stmt)]

        return self._execute(handler)

    def duration_histogram(self, query: EventQuery) -> List[Dict[str, Any]]:
        labels_and_conds = [
            ("<200ms", Event.duration_ms < 200),
            ("200-500ms", and_(Event.duration_ms >= 200, Event.duration_ms < 500)),
            ("500ms-1s", and_(Event.duration_ms >= 500, Event.duration_ms < 1000)),
            ("1-2s", and_(Event.duration_ms >= 1000, Event.duration_ms < 2000)),
            ("2-5s", and_(Event.duration_ms >= 2000, Event.duration_ms < 5000)),
            ("5-10s", and_(Event.duration_ms >= 5000, Event.duration_ms < 10000)),
            ("10-30s", and_(Event.duration_ms >= 10000, Event.duration_ms < 30000)),
            (">=30s", Event.duration_ms >= 30000),
        ]

        def handler(session: Session) -> List[Dict[str, Any]]:
            stmt = select(
                *[func.coalesce(func.sum(case((cond, 1), else_=0)), 0).label(f"b{index}") for index, (_label, cond) in enumerate(labels_and_conds)]
            ).where(*self._where(query))
            row = session.execute(stmt).one()
            return [
                {"name": label, "total_calls": int(_num(getattr(row, f"b{index}")))}
                for index, (label, _cond) in enumerate(labels_and_conds)
            ]

        return self._execute(handler)

    def filter_options(self, query: EventQuery) -> Dict[str, List[str]]:
        def _distinct(session: Session, column) -> List[str]:
            stmt = (
                select(column)
                .where(*self._where(query, ignore_dimension=True), column.is_not(None))
                .distinct()
                .order_by(column)
            )
            return [value for (value,) in session.execute(stmt).all() if value]

        def handler(session: Session) -> Dict[str, List[str]]:
            return {
                "domains": _distinct(session, Event.domain),
                "platforms": _distinct(session, Event.platform),
                "environments": _distinct(session, Event.environment),
                "results": _distinct(session, Event.result),
                "command_names": _distinct(session, Event.command_name),
                "input_sources": _distinct(session, Event.input_source),
                "cli_versions": _distinct(session, Event.cli_version),
            }

        return self._execute(handler)

    def events(self, query: EventQuery, limit: int, offset: int) -> Tuple[List[Dict[str, Any]], int]:
        def handler(session: Session) -> Tuple[List[Dict[str, Any]], int]:
            conds = self._where(query)
            total = session.execute(select(func.count()).select_from(Event).where(*conds)).scalar_one()
            stmt = select(Event).where(*conds).order_by(Event.event_time.desc()).limit(limit).offset(offset)
            items = [_serialize_orm(row) for row in session.execute(stmt).scalars().all()]
            return items, int(total)

        return self._execute(handler)


def _serialize_orm(row: Event) -> Dict[str, Any]:
    return {
        "id": row.id,
        "event_id": row.event_id,
        "event_time": to_iso(row.event_time),
        "cli_version": row.cli_version,
        "domain": row.domain,
        "platform": row.platform,
        "command": row.command,
        "command_name": row.command_name,
        "duration_ms": row.duration_ms,
        "api_duration_ms": row.api_duration_ms,
        "api_calls": row.api_calls,
        "input_source": row.input_source,
        "output_format": row.output_format,
        "result": row.result,
        "exit_code": row.exit_code,
        "environment": row.environment,
        "error_category": row.error_category,
        "error_code": row.error_code,
        "args_detail": row.args_detail,
        "user_id": row.user_id,
        "user_cn_name": row.user_cn_name,
        "user_long_id": row.user_long_id,
        "org_dept_code4": row.org_dept_code4,
        "org_dept_name4": row.org_dept_name4,
        "org_dept_code5": row.org_dept_code5,
        "org_dept_name5": row.org_dept_name5,
        "org_dept_code6": row.org_dept_code6,
        "org_dept_name6": row.org_dept_name6,
    }
