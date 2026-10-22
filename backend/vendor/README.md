# Vendored OpenBB provider (amazingdata)

Source: `galaxy-core/packages/openbb-provider-amazingdata`
vendored at galaxy-core commit `ca275b2`
(`feat(openbb): P2 provider package with EquityHistorical fetcher`).

Why vendored instead of pip dep: the upstream package pins
`openbb-core>=2.0` while this app pins `openbb-core==1.4.8`
(akshare/tushare plugins are 1.x-only). The fetcher only uses
stable `Fetcher/QueryParams/Data` + `EmptyDataError` APIs, verified
working on 1.4.8 — the pin is conservative, not real.

Sync rule: when galaxy-core updates the fetcher, re-copy
`src/openbb_provider_amazingdata/` over this directory and bump
the commit hash above. No local edits except the core-pin relax.
