# galaxy-web

> Finanalyzer 纯前端 — fork [finanalyzer/app](https://github.com/finanalyzer/app)（开源版 OpenBB Workspace）。
> 上游跟踪 finanalyzer/app，只做适配不重写（widget 契约兼容，开箱即用）。

## 架构

```
浏览器 (Chrome, localStorage 存连接)
  │ 同源 /cn/* /hk/* /udf/* /v1/* /widgets.json (vite proxy 转发, 避 CORS)
  ↓
Finanalyzer SPA (本仓, dev :5174)
  │ HTTP (VITE_BACKEND_URL, 默认 http://lenovo:8000)
  ↓
galaxy-core services/http (FastAPI, lenovo:8000, 需 Bearer APP_API_KEY)
  │ SQL: amazingdata fetcher / _db.py 直读本地库 (只用 amazingdata, 不调 akshare/东财/雪球)
  ↓
galaxy-core PostgreSQL/TimescaleDB (lenovo 本地 5432, galaxy 库)
```

- galaxy-core = 纯后端（采集 + 存储 + provider 库 + HTTP widget API）；galaxy-web = 纯前端。
- 数据源：只用 amazingdata 本地库。A 股全链路本地；港股（hk/*）本地无覆盖，显示 Loading 为预期行为。
- 操作手册见 [docs/](./docs/)：连接、仪表盘、联动、排障。

## 端口与环境变量

| 用途       | 地址 / 值                        | 说明                                              |
|------------|----------------------------------|---------------------------------------------------|
| 前端 dev   | `http://127.0.0.1:5174`          | `pnpm dev`，vite proxy 转发后端，浏览器同源访问   |
| 后端       | `http://lenovo:8000`             | Tailscale 域名，需直连（见 docs/03-proxy.md）       |
| 后端鉴权   | `Authorization: Bearer w0-local-smoke` | lenovo `.env` 的 `APP_API_KEY`，dev key         |
| `VITE_BACKEND_URL` | `http://lenovo:8000`      | `.env.local`（已 gitignore），vite proxy 目标      |
| `VITE_API_BASE_URL` | 空                        | 直连时代残留，保持空，走 proxy 同源               |

## 快速开始

```bash
pnpm install && pnpm dev   # http://127.0.0.1:5174
```

1. 开终端代理豁免 tailscale：`source ~/.config/xray/proxy.bash`（`NO_PROXY` 须含 `lenovo,100.64.0.0/10`，见 docs/03-proxy.md）。
2. 浏览器开 `http://127.0.0.1:5174/#/connections` 按 [docs/01-connection.md](./docs/01-connection.md) 建连接。
3. 进仪表盘按 [docs/02-dashboard.md](./docs/02-dashboard.md) 操作。

后端部署见 galaxy-core `services/http/`（本仓不含后端）。

## 本仓行为约定（与上游的差异）

- 添加小组件时自动注入当前连接的 `connectionUrl/authentication`（`DashboardCanvas.handleAddWidgetsFromMenu`），否则新件发不出请求。
- 仪表盘级市场白名单 `markets`（如 `["cn"]`）：添加菜单只列白名单内 widget，非白名单拦截，空盘首件自动定白名单并持久化。
- 同 tab 同 widgetId 重复添加被拦截（弹字提示，零 POST）。
- 全局 ticker 条：顶部 `全局标的 (N)` 输入回车全盘同步，值写入各 widget `data.params[].value/default` 并 PUT 持久化；不一致时显示 `当前N个值未统一`。
- 参数初始化优先级：内存当前值 > 实例存值（`value`）> 定义默认值（`default`）。
- K 线（`cn/candles`）用 recharts 真蜡烛图（plotly bdata 解码 OHLC），>30 点自动 Brush 缩放。
- 网络失败不重试（`TypeError`），指数退避；tickers 缓存 5min。
