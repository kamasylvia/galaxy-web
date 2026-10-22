# 01 — 连接（Connections）

连接存在浏览器 `localStorage`（key `finanalyzer_connections`），**换浏览器/换机器要重建**。仪表盘在后端共享，连接在各浏览器本地隔离，这是预期行为。

## 新建连接

1. 开 `http://127.0.0.1:5174/#/connections` → 点 **Add**。
2. 填写：
   - **Name**：任意（如后端名）。
   - **URL**：`http://127.0.0.1:5174` —— 必须填本机 proxy 同源地址，**不要**直填后端地址（后端 CORS 未放行 dev 源，直连被浏览器拦）。
   - **Validate Widgets**：Yes。
   - **Authentication Type**：选 **Custom** → Add authentication field：
     - Key：`Authorization`
     - Value：`Bearer <APP_API_KEY>`（后端 `.env` 的 `APP_API_KEY`）
     - Location：`header`
3. 点 **Test Connection**：应显示 widgets 数量（与后端 `/api/widgets.json` 注册数一致）→ 再点 **Add**。

## 验证

- 列表显示 `Connected`，`Widgets: N`。
- `#/widgets` 页 Backend Widgets (N)。
- 任一 dashboard 的 widget 出数。

## 排障

| 现象 | 原因 | 解法 |
|------|------|------|
| Test 报 `Failed to fetch` | 终端代理吃了内网流量，或 proxy 目标不可达 | 先 `curl` 直连后端 `VITE_BACKEND_URL`；用代理则做豁免（见 03-proxy.md） |
| `/api/v1/dashboard` 401 | header 鉴权没配或 key 错 | 检查 Custom header 与后端 `APP_API_KEY` 一致 |
| 后端全 hang（连健康检查超时） | 后端 worker 卡死 | 上后端机 `kill -9 <uvicorn>` 重起服务 |
