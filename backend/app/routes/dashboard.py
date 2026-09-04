# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
看板接口。
"""
import logging

from flask import Blueprint, jsonify, request

from app.services.dashboard_service import (
    get_commands,
    get_events,
    get_filter_options,
    get_overview,
    get_quality,
    get_users,
)
from app.utils.validators import parse_event_query, parse_limit_offset

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
