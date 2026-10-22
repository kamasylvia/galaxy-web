# 04 — 开发与排障（Dev & Troubleshooting）

## 本地开发

```bash
pnpm install
pnpm dev          # http://127.0.0.1:5174 (vite proxy -> VITE_BACKEND_URL，默认 http://lenovo:8000)
pnpm build        # tsc + vite build，产物 dist/
npx tsc -b        # 类型检查（提交前必过）
npx vitest run tests/connectionService.test.ts  # 联调相关单测
```

`.env.local`（已 gitignore）：

```
VITE_BACKEND_URL=http://lenovo:8000
VITE_API_BASE_URL=
```

## 后端（lenovo 仓 galaxy-core `services/http`，ssh 修）

```bash
ssh lenovo
cd /home/laniakea/development/galaxy-quant/galaxy-core/services/http
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

- 数据源铁律：只用 amazingdata 本地库。`fin_data/_db.py` 的 `to_records()` 统一洗 NaN/None/date→ISO，空表回 `[]`（不再 500）。
- `routes/equity_cn.py` 的 widget 定义即菜单来源（含 `gridData` 尺寸、`params` 默认值、`optionsEndpoint`）。
- 备份习惯：改前 `cp file /tmp/file.bak`。

## 常见故障对照

| 现象 | 定位 | 修法 |
|------|------|------|
| 页面 widget `No content / No data` | widget `data` 缺 `widgetId/connectionUrl`（菜单添加旧 bug） | 删了重加（现已自动注入）；存量用脚本回填 |
| 参数下拉 `Failed to fetch options` | `cn/tickers` 500（曾走 akshare 上游） | 已改本地 `stock_basic`；再现查后端日志 |
| `cn/quote` hang | 雪球 token 无效（`w0-local-smoke` 假 key） | 已改 amazingdata；勿加回 xq 路径 |
| K 线 `No chart data` + 500 | ticker 带 `.SH` 后缀旧值 / 库无此股（如 600001） | 默认已改 600028；新盘检查 ticker 值 |
| `/cn/lhb?limit=20` 500 | `trade_date` 为 date 对象 + 行内 NaN，`json.dumps` 炸 | 已加 `to_records`；再现用 TestClient 拿 traceback（`raise_server_exceptions=True`） |
| 强刷后 ticker 打回原形 | 参数初始化曾取 `default` 盖掉 `value` | 已改 `value` 优先 + 同步写 `default`；存量已对齐 |
| 36 件盘 `Failed to fetch` 雪崩 | 浏览器并发打满 dev server + React Query 重试放大 | 网络失败不重试 + 退避；tickers 缓存 5min；生产用 build 包 |
| `PUT widget` 404 | id 含 `/` 被路由截断 | 后端已用 `{widget_id:path}`；前端传裸 id 即可 |

## 新开 dashboard 全绿检查表

```bash
K="Authorization: Bearer w0-local-smoke"
for e in "cn/quote?ticker=600325" "cn/key_metrics?ticker=600325" "cn/candles?ticker=600028&interval=day&interval_multiplier=1&start_date=2025-09-01&end_date=2025-09-05" "cn/tickers" "cn/lhb?ticker=600325&limit=20"; do
  curl -s -m15 -H "$K" "http://127.0.0.1:5174/$e" -o /dev/null -w "$e -> %{http_code}\n"
done
# 全 200 即后端 OK；UI 仍红 = 前端 data 缺连接上下文，删了重加
```
