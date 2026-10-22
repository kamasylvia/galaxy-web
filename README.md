# galaxy-web

> Finanalyzer 纯前端 — fork [finanalyzer/app](https://github.com/finanalyzer/app)(开源版 OpenBB Workspace)。
> 上游跟踪 finanalyzer/app，只做适配不重写(widget 契约兼容，开箱即用)。
> Леново 补丁:tiptap chunk 合并、dashboardApi 走连接 URL、创建仪表盘补桩(见各文件 `lenovo` 注释)。

## 布局

- `/` — Finanalyzer 前端(React + Vite SPA，`pnpm install && pnpm build`，产物 `dist/`)
- 后端不在本仓:galaxy-core `services/http/`(FastAPI widget API :8000,24 widgets + `/v1/dashboard`)

## 架构

```
Finanalyzer SPA (本仓, :4173)
   │ HTTP: /widgets.json + /cn/* + /v1/dashboard
   ↓
galaxy-core services/http (FastAPI, :8000)
   │ SQL: amazingdata fetcher / _db.py 直读
   ↓
galaxy-core PostgreSQL/TimescaleDB (本地 5432, galaxy 库)
```

- galaxy-core = 纯后端(采集 + 存储 + provider 库 + HTTP widget API);galaxy-web = 纯前端。
- A 股走本地库(`amazingdata` fetcher)，HK/实时链走 akshare。

## 快速开始

```bash
pnpm install && pnpm build   # dist/ 由 finanalyzer-app service 托管(:4173)
```

后端部署见 galaxy-core `services/http/docs/deploy.md`。NixOS 双 service：`finanalyzer-app`(本仓) + `galaxy-web`(galaxy-core `services/http`)。
