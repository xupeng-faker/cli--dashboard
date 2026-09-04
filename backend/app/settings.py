# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
按环境加载 YAML 配置并输出 settings 字典。
"""
import os
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

from app.utils.encoding import decode_value

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

__all__ = ["get_settings"]


def _get_current_env() -> str:
    env = os.getenv("FLASK_ENV", "local").lower()
    if env not in ("local", "test", "prod"):
        env = "local"
    return env


def _load_yaml(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as file_handle:
            data = yaml.safe_load(file_handle) or {}
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}


def get_settings() -> Dict[str, Any]:
    env = _get_current_env()
    cfg_file = "config_test.yaml" if env in ("local", "test") else "config_prod.yaml"
    cfg_path = os.path.join(CONFIG_DIR, cfg_file)
    cfg = _load_yaml(cfg_path)

    app_cfg = cfg.get("app", {})
    gauss_cfg = cfg.get("gaussdb", {})
    use_mock = bool(app_cfg.get("use_mock", True))

    settings: Dict[str, Any] = {
        "ENV_NAME": env,
        "LOG_LEVEL": str(app_cfg.get("log_level", "INFO")).upper(),
        "PORT": int(app_cfg.get("port", 5002)),
        "USE_MOCK": use_mock,
        "GAUSS_HOST": gauss_cfg.get("host", "127.0.0.1"),
        "GAUSS_PORT": int(gauss_cfg.get("port", 5432)),
        "GAUSS_USER": gauss_cfg.get("user", "root"),
        "GAUSS_PASSWORD": decode_value(os.getenv("GAUSS_PASSWORD", "")),
        "GAUSS_DATABASE": gauss_cfg.get("database", "postgres"),
        "GAUSS_SCHEMA": gauss_cfg.get("schema", "coreinfactory"),
        "GAUSS_SSLMODE": gauss_cfg.get("sslmode", "disable"),
    }
    return settings
