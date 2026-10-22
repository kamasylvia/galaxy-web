# 02 — 仪表盘与小组件（Dashboards & Widgets）

## 新建仪表盘

任一 App 卡片（如 A股）点一次即按模板新建一个 dashboard（`App 卡片 ≠ 仪表盘`，点一次建一个，侧栏 MY DASHBOARDS 可见）。或在 dashboard 页直接建空盘。

## 市场白名单 `markets`

- 仪表盘级字段（后端透存）：如 `["cn"]`。
- 添加菜单（Add Widgets）**只列**白名单内的 widget（内置 Chart/Table/… 永远可加，无市场归属的 `/udf` 也可加）。
- 非白名单件点添加直接拦截（弹字，不发 POST）。
- 空盘：加的第一个市场件自动定白名单并持久化。
- 改白名单：`PUT /v1/dashboard/{id}` body `{"markets":["cn","hk"]}`（或删空即不限）。

## 添加小组件

1. 进 dashboard → 右下角 **Add Widgets** → 选分类勾选 → **Add**。
2. 新件自动带当前连接上下文（`connectionUrl/authentication`），无需手动配。
3. 同 tab 同 widget 重复添加被拦截（`"…已在当前页，跳过重复添加"`，零 POST）。
4. 新件尺寸用后端 `gridData`（缺省 20×8）；存量挤扁件删了重加即正常。

## 全局标的联动

- dashboard 顶部 `全局标的 (N)`：输入 ticker 回车，全盘含 ticker 的 widget 同步重取。
- 同步值写入各 widget `data.params[].value/default` 并 PUT 持久化，强刷不丢。
- 值不一致时显示 `当前N个值未统一` + placeholder 预览各值。
- 单 widget 的 ticker 下拉同样触发全盘联动（Group 1 机制）。

## 排序建议（A股盘）

自选（quote）→ 简况（key_metrics/news）→ K线（candles）→ 行情（prices）→ 财报（financial_data/income/balance/cash_flow）→ 资金（lhb/block_trade/margin/sector_flow）→ 估值（industry_valuation）。

## 已知行为

- `hk/*` 在 amazingdata 无覆盖，显示 Loading 为预期（非 bug）。
- `cn/news` 对 A股回空数组，显示灰色 `No data available`（本地无新闻表，非 bug）。
- 后端路由 `PUT /v1/dashboard/{id}/widgets/{widget_id}` 的 id 含 `/` 时可用（`:path` 转换器）；前端传裸 id 即可。
