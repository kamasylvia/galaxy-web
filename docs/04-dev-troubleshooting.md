# 04 — 开发与排障（Dev & Troubleshooting）

## 本地开发

```bash
pnpm install
pnpm dev          # http://127.0.0.1:5174 (vite proxy -> VITE_BACKEND_URL)
pnpm build        # tsc + vite build，产物 dist/
npx tsc -b        # 类型检查（提交前必过）
npx vitest run tests/connectionService.test.ts  # 联调相关单测
```

`.env.local`（已 gitignore）：

```
VITE_BACKEND_URL=http://<backend-host>:8001
VITE_API_BASE_URL=
```

## 后端（另仓，自行替换路径/端口）

```bash
ssh <backend-host>
cd <repo>/services/http
uv run uvicorn main:app --host 0.0.0.0 --port 8001
```

- 数据源：只用本地库直读，不调外部行情上游。NaN/None/date 统一洗成 JSON-safe，空表回 `[]`（不再 500）。
- widget 定义即菜单来源（含 `gridData` 尺寸、`params` 默认值、`optionsEndpoint`）。
- 备份习惯：改前 `cp file /tmp/file.bak`。

## 常见故障对照

| 现象 | 定位 | 修法 |
|------|------|------|
| 页面 widget `No content / No data` | widget `data` 缺 `widgetId/connectionUrl` | 删了重加（现已自动注入）；存量用脚本回填 |
| 参数下拉 `Failed to fetch options` | tickers 接口 500（曾走外部上游） | 已改本地表；再现查后端日志 |
| quote hang | 快照 token 无效 | 已改本地库；勿加回外部快照路径 |
| K 线 `No chart data` + 500 | ticker 旧值 / 库无此股 | 检查 ticker 值；默认用有覆盖的股 |
| 某接口 500 | date 对象 + 行内 NaN，`json.dumps` 炸 | 已加统一清洗；再现用 TestClient 拿 traceback（`raise_server_exceptions=True`） |
| 强刷后 ticker 打回原形 | 参数初始化曾取 `default` 盖掉 `value` | 已改 `value` 优先 + 同步写 `default` |
| 多件盘 `Failed to fetch` 雪崩 | 浏览器并发打满 dev server + 重试放大 | 网络失败不重试 + 退避；tickers 缓存；生产用 build 包 |
| `PUT widget` 404 | id 含 `/` 被路由截断 | 后端用 `{widget_id:path}` 转换器；前端传裸 id 即可 |

## 新开 dashboard 全绿检查表

```bash
K="Authorization: Bearer <APP_API_KEY>"
for e in "api/v1/cn/quote?ticker=600325" "api/v1/cn/key_metrics?ticker=600325" "api/v1/cn/candles?ticker=600028&interval=day&interval_multiplier=1&start_date=2025-09-01&end_date=2025-09-05" "api/v1/cn/tickers" "api/v1/cn/lhb?ticker=600325&limit=20"; do
  curl -s -m15 -H "$K" "http://127.0.0.1:5174/$e" -o /dev/null -w "$e -> %{http_code}\n"
done
# 全 200 即后端 OK；UI 仍红 = 前端 data 缺连接上下文，删了重加
```
