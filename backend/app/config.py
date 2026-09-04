# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
Flask 配置类定义。
"""
import os

from dotenv import load_dotenv


def _load_dotenv_safely() -> None:
    try:
        load_dotenv()
    except OSError:
        return


_load_dotenv_safely()


class Config:
    """基础配置类。"""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-production")
    JSON_AS_ASCII = False


class LocalConfig(Config):
    """本地开发环境配置。"""

    DEBUG = True
    TESTING = False


class TestConfig(Config):
    """测试环境配置。"""

    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    """生产环境配置。"""

    DEBUG = False
    TESTING = False


_CONFIG_MAP = {"local": LocalConfig, "test": TestConfig, "prod": ProductionConfig}


def get_config_class(env_name: str):
    """
    根据环境名称获取配置类。

    Args:
        env_name: 环境名称 (local/test/prod)

    Returns:
        配置类
    """
    return _CONFIG_MAP.get(env_name, LocalConfig)
