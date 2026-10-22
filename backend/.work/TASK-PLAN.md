# galaxy-web 任务计划 — Finanalyzer 前端(fork openbb-hka)

> 对应 galaxy-core P3(前端适配)。galaxy-core 侧已交付:provider 包 + `obb_equity_historical` 视图 + 联调冒烟通过。
> 上游:https://github.com/finanalyzer/openbb-hka (59★,FastAPI 后端 + TS 前端,TradingView 图表)
> 新会话入口:读本文件 + galaxy-core `.work/openbb-finanalyzer/PLAN.md` §4。

## W0 fork 与基线验证 — 服务通,默认源挂(2026-10-21)

- [x] fork 落地:upstream remote 已加,`upstream/master == origin/master == 6338d11`,diff 零(本仓 fork 点即锁点)
- [x] 本地跑通:`uv sync`(py3.11.15)+ `uvicorn main:app`:`/health`、`apps.json`、`widgets.json`(19 个)OK;补 gitignored `.env` + `~/.openbb_platform/user_settings.json`(akshare credential 走 OpenBB settings,不读本仓 `.env`)
- [ ] A-Shares 三模块默认源(akshare)出数 — ❌ 本环境全挂(非本仓代码问题):prices/candles/income 等全 500,根因 `chinese_calendar` 只支持 2004–2025 而今天 2026-10-21(任何触今日的调用即 `NotImplementedError`);`cn/tickers` 另有 `query.sse.com.cn` SSLError。→ W1 切 amazingdata 即绕过
- [x] galaxy-core provider 可达:web venv 直调 fetcher `600000.SH 2025-10-01~20 → 8 行`;`obb_equity_historical` 15,516,192 行 max 2026-10-20;`/tmp/obb-venv`(core 2.0.1)router 冒烟 242 行
- 残留:`tests/test_main.py` import 命中 site-packages 同名 `main`(py_mini_racer),`PYTHONPATH=.` 可绕,属上游测试问题,W1 不动

## W1 Stock Price 切 amazingdata(首个打通) — ✅ 完成(2026-10-21)

- [x] provider 接入:直调 `AmazingDataEquityHistoricalFetcher`(不走 `obb` router——openbb 4.1.3 的 `openbb/package/*` 是构建时静态白名单,entry-point 装上也认不出;provider 包要求的 `openbb-core>=2.0` 与本仓 `1.4.8` 冲突,故不作 pip 依赖,走 `sys.path` 挂载 `../galaxy-core/.../src`,运行依赖只加 `asyncpg`)
- [x] `fin_data/profile.get_historical_prices` + `routes/charts.get_chart_data`:A 股(SH/SZ/BJ,裸码经 `normalize_symbol`→后缀)走 amazingdata 主,akshare 备;HK/US 维持默认链
- [x] venv 3.11→3.12(`.python-version` + `requires-python>=3.12`;上游要求 `>=3.11`,不锁死);`uv.lock` 重建
- [x] 冒烟:`600000.SH/600325/000002` 日线各 22 行;HTTP 端到端 prices+candles 出数;无数据(`600001.SH` 退市/未来区间)→ `EmptyDataError`,语义正确
- [x] 决策记录:openbb 4.x 静态 router 白名单问题 → 后续 W2/W3 凡读 amazingdata 一律直调 fetcher,不碰 router
- [x] openbb-core 升级评估(2026-10-21,结论=不升):core 2.0.1 router 虽是动态白名单(认 amazingdata),但 `openbb-akshare` 最新 1.2.5 仍 pin `openbb-core<2.0`+`openbb==4.7.1`(PyPI 实测;`pip index` 报的 5.0.0 系脏数据),`openbb 5.0.0` 依赖表已无 akshare/tushare——升 core 即断 HK/Financials/Profile 默认链。维持 `openbb-core==1.4.8` + 直调 fetcher(2026-10-21 回滚验证:prices 22 行+suite 10 passed)

## W2 Profile/Financials 映射 — ✅ 部分完成(2026-10-21;HTTP 端到端出数,suite 10 passed)
- [x] Profile/info ← `stock_basic` 直读(`fin_data/_db.py` asyncpg 层):600325 出数(公司/简称/上市2004-02-25/主板);HK 维持默认链
- [x] income/cash_flow ← 库表直读(`tot_opera_rev→总营收`、`total_profit→利润总额`诚实列名;`statement_type='1'`合并口径;annual→12-31);600325 年报 2025 营收 834 亿
- [ ] balance ← 保持 akshare(库表 17 列窄表无总量;缺口:galaxy-core 补采 `total_assets/total_liab/total_equity`+income `parent_netprofit`)
- [ ] financial_data/quote/tickers/news:实时/搜索类,保持 akshare(无库表)

## W3 A 股特色 widgets — ✅ 完成(2026-10-21;5 个端点 HTTP 出数,widgets 19→24,suite 10 passed)

- [x] `cn/industry_valuation` ← industry_daily:申万 index_code + PB/PE(农林牧渔 801010.SI 9 月 pb 2.59/pe 18.5)
- [x] `cn/sector_flow` ← akshare_sector_fund_flow_daily:板块主力净流入快照(当日行净额 null 系采集时序,取多日即有数)
- [x] `cn/lhb` ← long_hu_bang:席位买卖明细(600325 9-21 高盛席位,涨跌偏离 10.08%)
- [x] `cn/block_trade` ← block_trading:大宗明细;`cn/margin` ← margin_detail_daily:两融余额(600325 10-19 余额 4.97 亿)
- [x] market_code 带后缀(symbol_f 直匹,零转换);空数据→KeyError→500(与既有语义一致)
- [x] 注:直读库表,未走 provider fetcher(本仓 widgets 是 FastAPI 直调;galaxy-core P3 的 fetcher/视图是 Workspace 经 obb router 消费时才需要,待联调时补)

## 待 galaxy-core 补(需求单,2026-10-21;复查 2026-10-21)

- [x] G2 income `parent_netprofit` ✅ 另一会话已回填(migration 30:`net_pro_excl_min_int_inc`;本仓已切 `净利润` 列,600325 年报 2025 归母 -95 亿)
- [x] G1 balance `total_equity` ✅ 另一会话已补少股列(`minority_equity`+`tot_share_equity_incl_min_int`,4e7e742);恒等式分毫不差;本仓 `get_balance` 已切库表(600325 年报 2025 权益 1093 亿)
- [ ] G3(待联调)provider fetcher:Income/Balance/Cash/Profile/Industry/Margin/LHB/BlockTrade 经 `obb` router 消费的 fetcher+视图(本仓直读已通,联调才需要)

## W4 部署 — ✅ 双轨就绪(2026-10-21)

- [x] W4a provider 转正:vendor/ + `fin_data/provider.py` Fetcher 薄层;widgets 全经 Fetcher 接口;HTTP 全绿+suite 10 passed
- [x] G1/G2 闭环:balance/income 已切库表
- [x] Docker:镜像 `galaxy-web:w4` 构建成功并跑通(24 widgets);compose 就绪
- [x] NixOS 原生:galaxy-web service active+enabled;防火墙 8000+4173
- [x] 文档:`docs/deploy.md`+`env.example` 补 GALAXY_PG_*
- [x] W4b Finanalyzer 前端上线:独立仓 `~/development/finanalyzer-app`(不进本仓 git);`finanalyzer-app` service(:4173) active;LAN/Tailscale 双可达
- [ ] 联调:前端"连接"页加后端 → A股三模块出数(G3 fetcher 注册,需实测)

## 约定

- 本仓只做适配不重写;上游更新 cherry-pick,冲突段落以上游为准
- provider 缺数一律回 galaxy-core 实现,不在本仓直连 PG(架构红线)
- 验收:每个 widget 截图 + 数据行数对账(galaxy-core 为准)
