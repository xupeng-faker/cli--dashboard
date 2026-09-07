# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
健康检查接口。
"""
import logging

from flask import Blueprint, current_app, jsonify

from app.db.opengauss_connection import ping_database

logger = logging.getLogger(__name__)

bp = Blueprint("health", __name__)

__all__ = ["bp"]


@bp.get("/")
def health():
    use_mock = bool(current_app.config.get("USE_MOCK"))
    payload = {
        "status": "ok",
        "data_source": "mock" if use_mock else "gaussdb",
    }
    if not use_mock:
        payload["database"] = "ok" if ping_database() else "error"
        if payload["database"] != "ok":
            payload["status"] = "degraded"
    logger.debug("Health check request received")
    return jsonify(payload)
