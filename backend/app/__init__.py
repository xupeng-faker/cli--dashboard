# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
Flask 应用工厂。
"""
import logging
from logging.config import dictConfig

from flask import Flask, jsonify
from flask_cors import CORS

from .config import get_config_class
from .db.opengauss_connection import init_database
from .routes.dashboard import bp as dashboard_bp
from .routes.health import bp as health_bp
from .settings import get_settings
from .utils.errors import APIError

__all__ = ["create_app"]

logger = logging.getLogger(__name__)


def _configure_logging(log_level: str) -> None:
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "loggers": {
                "werkzeug": {"handlers": ["wsgi"], "level": "WARNING", "propagate": False},
                "app": {"handlers": ["wsgi"], "level": log_level, "propagate": False},
            },
            "root": {"level": log_level, "handlers": ["wsgi"]},
        }
    )


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_404(_error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        logger.exception("Unexpected error occurred: %s", str(error))
        return jsonify({"error": "An unexpected error occurred"}), 500


def create_app() -> Flask:
    app = Flask(__name__)
    settings = get_settings()

    _configure_logging(settings["LOG_LEVEL"])
    app.logger.info("Initializing CLI dashboard backend service")

    config_class = get_config_class(settings["ENV_NAME"])
    app.config.from_object(config_class)
    app.config.update(settings)

    CORS(app, resources={r"/cli_api/.*": {"origins": "*"}})
    init_database(app)

    app.register_blueprint(health_bp, url_prefix="/cli_api/health")
    app.register_blueprint(dashboard_bp, url_prefix="/cli_api/dashboard")
    _register_error_handlers(app)

    app.logger.info(
        "CLI dashboard backend initialized. data_source='%s'",
        "mock" if settings["USE_MOCK"] else "gaussdb",
    )
    return app
