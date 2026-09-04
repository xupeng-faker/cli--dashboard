# Copyright 2026 Huawei Technologies Co., Ltd. All rights reserved
"""
WSGI 启动入口。
"""
import os

from app import create_app
from app.settings import get_settings

settings = get_settings()
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", settings["PORT"]))
    app.run(host="0.0.0.0", port=port)
