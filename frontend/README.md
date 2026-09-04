# CoreToolCLI 数据看板

面向 CoreToolCLI 指令打点的运营看板，用来看**调用量、活跃用户、成功率、耗时、运行系统和错误**。数据表为高斯数据库 `coreinfactory.cli_command_event`。

技术栈对齐 [honorHall](file:///Users/fakertony/Documents/cursor/honorHall)：

- 后端：Python 3.9+、Flask 3.0.0、SQLAlchemy 2.0.36、Flask-CORS 4.0.0
- 前端：Node.js 18、Vue 3.5、Vite 6、TypeScript 5.6、Pinia 3、Axios 1.13、ECharts 5

单页深色大屏（1920×1080 等比缩放），不是后台管理系统。

## 本地快速启动（样例数据）

默认不连高斯库，后端用内存样例数据，便于先把页面和指标跑通。

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=local
python wsgi.py
```

```bash
# 前端（另开终端）
cd frontend
npm install
npm run dev
```

浏览器打开 http://127.0.0.1:5174

## 连接高斯数据库

1. 修改 `backend/config/config_test.yaml`（本地）或 `config_prod.yaml`（生产）：
   - `app.use_mock: false`
   - 填写 `gaussdb.host / port / user / database / schema`
2. 在 `backend/` 下执行 `python -m scripts.encode_password`，将库密码写入 `.env`
3. 重启后端

## 页面

单屏运行态势：调用量、活跃用户、成功率、耗时、执行结果、运行系统、领域、热门指令、错误分类、近期事件。右上角可切今日 / 近 7 天 / 近 30 天，数据每 30 秒刷新。
