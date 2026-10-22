"""Direct TimescaleDB reads for A-share widgets (galaxy-core data layer).

Bypasses the obb 1.4.8 static router whitelist the same way
``profile._amazingdata_prices`` does. PG connection env mirrors the
openbb-provider-amazingdata fetcher (GALAXY_PG_* > local defaults).
"""

import asyncio
import concurrent.futures
import os

import asyncpg
import pandas as pd


def _connect_kwargs() -> dict:
    return {
        "host": os.getenv("GALAXY_PG_HOST", "127.0.0.1"),
        "port": int(os.getenv("GALAXY_PG_PORT", "5432")),
        "database": os.getenv("GALAXY_PG_DB", "galaxy"),
        "user": os.getenv("GALAXY_PG_USER", "postgres"),
        "password": os.getenv("GALAXY_PG_PASSWORD", "postgres"),
    }


def _run(coro):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


async def _fetchrow(sql: str, *args):
    conn = await asyncpg.connect(**_connect_kwargs())
    try:
        return await conn.fetchrow(sql, *args)
    finally:
        await conn.close()


async def _fetch(sql: str, *args):
    conn = await asyncpg.connect(**_connect_kwargs())
    try:
        return await conn.fetch(sql, *args)
    finally:
        await conn.close()


def fetch_profile(symbol_f: str) -> pd.DataFrame:
    """One row from stock_basic, shaped like the old akshare profile frame."""
    row = _run(_fetchrow(
        "SELECT symbol, security_name, comp_name, list_date, delist_date,"
        " listplate_name, is_listed FROM stock_basic WHERE symbol = $1",
        symbol_f,
    ))
    if row is None:
        raise KeyError(f"no stock_basic row for {symbol_f}")
    d = dict(row)
    return pd.DataFrame([{
        "symbol": d["symbol"],
        "公司名称": d["comp_name"] or d["security_name"],
        "证券简称": d["security_name"],
        "上市日期": d["list_date"],
        "退市日期": d["delist_date"],
        "板块": d["listplate_name"],
        "在市": d["is_listed"],
    }])


def _to_date(v: str):
    from datetime import date as _date
    return _date(*[int(x) for x in v.split("-")])


def fetch_industry_valuation(index_code: str | None, start_date: str, end_date: str, limit: int) -> pd.DataFrame:
    """Industry index daily bars with PB/PE (申万 index_code like 801010.SI)."""
    if index_code:
        rows = _run(_fetch(
            "SELECT trade_date, index_code, open, high, low, close, volume, amount,"
            " pb, pe FROM industry_daily WHERE index_code = $1"
            " AND trade_date >= $2 AND trade_date <= $3"
            " ORDER BY trade_date DESC LIMIT $4",
            index_code, _to_date(start_date), _to_date(end_date), limit,
        ))
    else:
        rows = _run(_fetch(
            "SELECT trade_date, index_code, close, pb, pe FROM industry_daily"
            " WHERE trade_date >= $1 AND trade_date <= $2"
            " ORDER BY trade_date DESC, index_code LIMIT $3",
            _to_date(start_date), _to_date(end_date), limit,
        ))
    if not rows:
        raise KeyError(f"no industry_daily rows for {index_code}")
    return pd.DataFrame([dict(r) for r in rows])


def fetch_sector_flow(trade_date: str | None, limit: int) -> pd.DataFrame:
    """Sector fund-flow snapshot (AKShare sector flow mirror table)."""
    if trade_date:
        rows = _run(_fetch(
            "SELECT * FROM akshare_sector_fund_flow_daily WHERE trade_date = $1"
            " ORDER BY main_net_amount DESC NULLS LAST LIMIT $2",
            _to_date(trade_date), limit,
        ))
    else:
        rows = _run(_fetch(
            "SELECT * FROM akshare_sector_fund_flow_daily"
            " ORDER BY trade_date DESC, main_net_amount DESC NULLS LAST LIMIT $1",
            limit,
        ))
    if not rows:
        raise KeyError("no sector fund-flow rows")
    return pd.DataFrame([dict(r) for r in rows])


def fetch_lhb(symbol_f: str, limit: int) -> pd.DataFrame:
    """Long-hu-bang (dragon-tiger board) records for one stock, newest first."""
    rows = _run(_fetch(
        "SELECT trade_date, security_name, trader_name, flow_mark,"
        " reason_type_name, change_range, buy_amount, sell_amount,"
        " total_amount, total_volume FROM long_hu_bang WHERE market_code = $1"
        " ORDER BY trade_date DESC LIMIT $2",
        symbol_f, limit,
    ))
    if not rows:
        raise KeyError(f"no long_hu_bang rows for {symbol_f}")
    return pd.DataFrame([dict(r) for r in rows])


def fetch_block_trade(symbol_f: str, limit: int) -> pd.DataFrame:
    """Block trading records for one stock, newest first."""
    rows = _run(_fetch(
        "SELECT trade_date, b_buyer_name, b_seller_name, b_share_price,"
        " b_share_volume, b_share_amount FROM block_trading WHERE market_code = $1"
        " ORDER BY trade_date DESC LIMIT $2",
        symbol_f, limit,
    ))
    if not rows:
        raise KeyError(f"no block_trading rows for {symbol_f}")
    return pd.DataFrame([dict(r) for r in rows])



def fetch_margin(symbol_f: str, limit: int) -> pd.DataFrame:
    """Margin trading daily detail for one stock, newest first."""
    rows = _run(_fetch(
        "SELECT trade_date, borrow_money_balance, purch_with_borrow_money,"
        " repayment_of_borrow_money, sec_lending_balance, sales_of_borrowed_sec,"
        " repayment_of_borrow_sec, margin_trade_balance"
        " FROM margin_detail_daily WHERE market_code = $1"
        " ORDER BY trade_date DESC LIMIT $2",
        symbol_f, limit,
    ))
    if not rows:
        raise KeyError(f"no margin_detail_daily rows for {symbol_f}")
    return pd.DataFrame([dict(r) for r in rows])
def fetch_statements(table: str, symbol_f: str, period: str, limit: int) -> pd.DataFrame:
    """Latest N reporting periods (newest first).

    statement_type='1' = consolidated (tushare comp_type=1 default).
    period: 'annual' -> Dec-31 rows only; else all periods newest-first.
    """
    if period == "annual":
        rows = _run(_fetch(
            f"SELECT * FROM {table} WHERE symbol = $1 AND statement_type = '1'"
            " AND EXTRACT(MONTH FROM reporting_period) = 12"
            " ORDER BY reporting_period DESC LIMIT $2",
            symbol_f, limit,
        ))
    else:
        rows = _run(_fetch(
            f"SELECT * FROM {table} WHERE symbol = $1 AND statement_type = '1'"
            " ORDER BY reporting_period DESC LIMIT $2",
            symbol_f, limit,
        ))
    if not rows:
        raise KeyError(f"no {table} rows for {symbol_f}")
    return pd.DataFrame([dict(r) for r in rows])
