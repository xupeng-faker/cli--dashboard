# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
看板接口。
"""
import logging

from flask import Blueprint, jsonify, request

from app.services.dashboard_service import (
    get_commands,
    get_departments,
    get_events,
    get_filter_options,
    get_overview,
    get_quality,
    get_users,
)
from app.utils.errors import ValidationError
from app.utils.validators import parse_event_query, parse_int, parse_limit_offset

logger = logging.getLogger(__name__)

bp = Blueprint("dashboard", __name__)

__all__ = ["bp"]


@bp.get("/overview")
def overview():
    query = parse_event_query(request.args)
    data = get_overview(query)
    logger.debug("Overview returned. calls '%s'", data["kpis"]["total_calls"]["value"])
    return jsonify(data)


@bp.get("/commands")
def commands():
    query = parse_event_query(request.args)
    return jsonify(get_commands(query))


@bp.get("/users")
def users():
    query = parse_event_query(request.args)
    return jsonify(get_users(query))


@bp.get("/departments")
def departments():
    query = parse_event_query(request.args)
    level = parse_int(request.args.get("level"), "level", 4, 6) or 4

    def department_name(name: str):
        value = str(request.args.get(name) or "").strip()
        if len(value) > 256:
            raise ValidationError("Invalid parameter", payload={"field": name})
        return value or None

    dept4 = department_name("dept4")
    dept5 = department_name("dept5")
    if level >= 5 and not dept4:
        raise ValidationError("Invalid parameter", payload={"field": "dept4"})
    if level >= 6 and not dept5:
        raise ValidationError("Invalid parameter", payload={"field": "dept5"})
    return jsonify(get_departments(query, level, dept4=dept4, dept5=dept5))


@bp.get("/quality")
def quality():
    query = parse_event_query(request.args)
    return jsonify(get_quality(query))


@bp.get("/events")
def events():
    query = parse_event_query(request.args)
    limit, offset = parse_limit_offset(request.args.get("limit"), request.args.get("offset"))
    return jsonify(get_events(query, limit=limit, offset=offset))


@bp.get("/filters")
def filters():
    query = parse_event_query(request.args)
    return jsonify(get_filter_options(query))
