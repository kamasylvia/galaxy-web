# galaxy-web

> Finanalyzer 前端 — fork [finanalyzer/app](https://github.com/finanalyzer/app)(开源版 OpenBB Workspace)，接本地 galaxy-core 数据。
> 上游跟踪 finanalyzer/app，只做适配不重写(widget 契约兼容，开箱即用)。

## 布局

- `/` — Finanalyzer 前端(React + Vite SPA，`pnpm install && pnpm build`，产物 `dist/`)
- `backend/` — widget HTTP API(FastAPI)：24 个 A 股 widgets(`/widgets.json`) + `/v1/dashboard`，数据来自本地 galaxy-core 库
- `backend/vendor/` — OpenBB provider 薄层(直调 galaxy-core 表，不走 `obb` router)

## 架构

```
Finanalyzer SPA (本仓根, :4173)
   │ HTTP: /widgets.json + /cn/* + /v1/dashboard
   ↓
backend/ FastAPI (本仓 backend/, :8000)
   │ SQL: amazingdata fetcher / _db.py 直读
   ↓
galaxy-core PostgreSQL/TimescaleDB (本地 5432, galaxy 库)
```

- galaxy-core 对外暴露的是 **OpenBB provider 库 + 数据**（无 HTTP 层；唯一的 uvicorn 是 gRPC echo `:50052`)，所以 Finanalyzer SPA 不能直连它 —— `backend/` 是必需的 widget HTTP 适配层，不是专有后端。
- A 股走本地库(`amazingdata` fetcher)，HK/实时链走 akshare。

## 快速开始

```bash
# 前端
pnpm install && pnpm build   # dist/ 由 finanalyzer-app service 托管(:4173)

# 后端
cd backend && uv sync && uv run uvicorn main:app --reload  # :8000
```

部署见 `backend/docs/deploy.md`。NixOS 双 service：`finanalyzer-app`(本仓根) + `galaxy-web`(backend/)。
