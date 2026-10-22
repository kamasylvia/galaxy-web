# galaxy-web

> Finanalyzer 纯前端 — fork [finanalyzer/app](https://github.com/finanalyzer/app)（开源版 OpenBB Workspace）。
> 上游跟踪 finanalyzer/app，只做适配不重写（widget 契约兼容，开箱即用）。

## 架构

```
浏览器 (Chrome, localStorage 存连接)
  │ 同源 /api/* (vite proxy 转发, 避 CORS)
  ↓
Finanalyzer SPA (本仓, dev :5174)
  │ HTTP (VITE_BACKEND_URL, 如 http://<backend-host>:8001)
  ↓
widget 后端 (FastAPI, 全 /api 前缀, 需 Bearer APP_API_KEY)
  │ SQL: 本地库直读 (不调外部行情上游)
  ↓
PostgreSQL/TimescaleDB (后端本地, galaxy 库)
```

- 后端 = 纯后端（采集 + 存储 + provider 库 + HTTP widget API）；本仓 = 纯前端。
- 后端需提供 `GET /api/widgets.json`（widget 注册表）、`/api/v1/*`（数据与 dashboard API）。无裸路由（`/widgets.json` 等已下线）。
- 操作手册见 [docs/](./docs/)：连接、仪表盘、联动、排障。

## 端口与环境变量

| 用途       | 值 | 说明 |
|------------|----|------|
| 前端 dev   | `http://127.0.0.1:5174` | `pnpm dev`，vite proxy 转发后端，浏览器同源访问 |
| 后端       | `VITE_BACKEND_URL`（如 `http://<backend-host>:8001`） | 浏览器填连接 URL 时填本机 proxy 同源地址（见 docs/01），直连后端地址只用于 proxy 目标 |
| 后端鉴权   | `Authorization: Bearer <APP_API_KEY>` | 后端 `.env` 的 `APP_API_KEY` |
| `VITE_BACKEND_URL` | 后端地址 | `.env.local`（已 gitignore），vite proxy 目标 |
| `VITE_API_BASE_URL` | 空 | 保留位，保持空，走 proxy 同源 |

## 快速开始

```bash
pnpm install && pnpm dev   # http://127.0.0.1:5174
```

1. 在 `.env.local` 配好 `VITE_BACKEND_URL`（后端地址），重启 dev server。
2. 浏览器开 `http://127.0.0.1:5174/#/connections` 按 [docs/01-connection.md](./docs/01-connection.md) 建连接。
3. 进仪表盘按 [docs/02-dashboard.md](./docs/02-dashboard.md) 操作。
4. 终端开代理且后端走内网域名/IP 时，先做代理豁免（仅特殊网络环境需要，见 docs/03-proxy.md）。
后端部署见后端仓 `services/http/`（本仓不含后端）。

## 本仓行为约定（与上游的差异）

- 添加小组件时自动注入当前连接的 `connectionUrl/authentication`（`DashboardCanvas.handleAddWidgetsFromMenu`），否则新件发不出请求。
- 仪表盘级市场白名单 `markets`（如 `["cn"]`，存 dashboard 元数据）：添加菜单只列白名单内 widget，非白名单拦截，空盘首件自动定白名单并持久化。菜单顶部可切换 scope。
- 同 tab 同 widgetId 重复添加被拦截（弹字提示，零 POST）。
- 全局 ticker 条：顶部 `全局标的 (N)` 输入回车全盘同步，值写入各 widget `data.params[].value/default` 并 PUT 持久化；不一致时显示未统一提示。
- 参数初始化优先级：内存当前值 > 实例存值（`value`）> 定义默认值（`default`）。
- K 线用 recharts 真蜡烛图（后端 plotly bdata 解码 OHLC），>30 点自动 Brush 缩放。
- 网络失败不重试（`TypeError`），指数退避；tickers 缓存 5min。
- 后端 `/api` 前缀收敛：连接发现（widgets/agents/apps/prompts.json）、dashboard、agent、proxy 转发统一走 `/api/*`，裸路由已删；缺 `/api` 前缀的相对 endpoint 前端自动补。
