# CoreToolCLI 数据看板

供 CLI 指令打点后的运营看板。读取高斯数据库 `coreinfactory.cli_command_event`，关注后续活跃量、调用量、运行系统和质量。

依赖版本对齐 honorHall：Python 3.9、Node.js 18、Flask 3.0、SQLAlchemy 2.0、Vue 3.5、Vite 6、Element Plus 2.13、Pinia 3、Axios 1.13。

## 启动

本地默认使用样例数据，不需要高斯库。

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=local
python wsgi.py
```

```bash
cd frontend
npm install
npm run dev
```

打开 http://127.0.0.1:5174

连真实库的步骤见 `backend/README.md`。
