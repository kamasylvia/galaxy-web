# 01 — 连接（Connections）

连接存在浏览器 `localStorage`（key `finanalyzer_connections`），**换浏览器/换机器要重建**。仪表盘在后端共享，连接在各浏览器本地隔离，这是预期行为。

## 新建连接（lenovo 后端）

1. 开 `http://127.0.0.1:5174/#/connections` → 点 **Add**。
2. 填写：
   - **Name**：`lenovo-8000`（任意）。
   - **URL**：`http://127.0.0.1:5174` —— 必须填本机 proxy 同源地址，**不要**直填 `http://lenovo:8000`（后端 CORS 未放行 5174，直连被浏览器拦）。
   - **Validate Widgets**：Yes。
   - **Authentication Type**：选 **Custom** → Add authentication field：
     - Key：`Authorization`
     - Value：`Bearer w0-local-smoke`（lenovo 后端 `.env` 的 `APP_API_KEY`，dev key）
     - Location：`header`
3. 点 **Test Connection**：应显示 widgets 24 个 → 再点 **Add**。

## 验证

- 列表显示 `Connected`，`Widgets: 24`。
- `#/widgets` 页 Backend Widgets (24)。
- 任一 dashboard 的 widget 出数。

## 排障

| 现象 | 原因 | 解法 |
|------|------|------|
| Test 报 `Failed to fetch` | 终端代理吃了 tailscale 流量 | `source ~/.config/xray/proxy.bash`，确认 `NO_PROXY` 含 `lenovo,100.64.0.0/10`（见 03-proxy.md） |
| `/v1/dashboard` 401 | header 鉴权没配或 key 错 | 检查 Custom header `Authorization: Bearer w0-local-smoke` |
| 后端全 hang（连 `/health` 超时） | lenovo worker 卡死（同步 akshare 阻塞曾致此） | ssh 上 lenovo `kill -9 <uvicorn>` 重起 `services/http` |
