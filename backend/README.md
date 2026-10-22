# galaxy-web

> Finanalyzer 前端 — fork [openbb-hka](https://github.com/finanalyzer/openbb-hka)(A 股 & 港股分析仪表盘),适配本地 galaxy-core 数据后端。
> 任务计划见 [.work/TASK-PLAN.md](.work/TASK-PLAN.md)。

## 定位

- 本仓 = **显示层**:OpenBB Workspace app(FastAPI 后端 + TS 前端,TradingView 图表)。
- 数据层 = galaxy-core(采集+存储+ `openbb-provider-amazingdata` provider)。**本仓永不直连 PG**(架构红线,provider 缺数回 galaxy-core 实现)。
- 上游跟踪 openbb-hka,只做适配不重写。

## 快速开始(待 W0 落地后补)

```bash
uv sync
uv run uvicorn main:app --reload
```
