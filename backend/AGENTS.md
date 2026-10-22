# AGENTS.md

> **本文档是项目约定主源(架构/适配/部署约定)。**

## Project Overview

galaxy-web 是 Finanalyzer 前端,fork 自 [openbb-hka](https://github.com/finanalyzer/openbb-hka)。
经 OpenBB provider(`amazingdata`,由 galaxy-core 提供)消费 A 股数据,渲染 Profile/Financials/Stock Price 三模块。

## 架构红线

- **本仓永不直连 PG**。所有数据经 provider fetcher;缺数回 galaxy-core 加视图+fetcher,不在本仓开直连。
- 上游只做适配不重写;上游更新 cherry-pick,冲突以上游为准。
- symbol 格式:上游裸代码(`000002`),本库带后缀(`600000.SH`)——映射层处理,见 TASK-PLAN W1。

## 任务进程

- 当前任务:`.work/TASK-PLAN.md`(W0→W4)。
- 数据侧计划与进度:galaxy-core `.work/openbb-finanalyzer/{PLAN,TASKS}.md`。
- 验收:每个 widget 截图 + 数据行数对账(galaxy-core 为准)。

## 已知坑

- galaxy-core `stock_basic.security_type` 存大类码(`EXTRA_STOCK_A`),kline 存市场码(`SH_A`)——Profile 映射注意口径。
