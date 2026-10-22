import pandas as pd
from openbb import obb
from . import default_provider

_AMAZINGDATA_MARKETS = ("SH", "SZ", "BJ")


def _a_share_fetch(fetcher, symbol_f: str, period: str, limit: int) -> pd.DataFrame:
    """Run a provider fetcher (transform -> extract -> transform) into a frame."""
    query = fetcher.transform_query({"symbol": symbol_f, "period": period, "limit": limit})
    rows = fetcher.extract_data(query, None)
    data = fetcher.transform_data(query, rows)
    return pd.DataFrame([d.model_dump(mode="json") for d in data])


def get_balance(ticker: str, period: str, limit: int) -> pd.DataFrame:
    """
    Get balance sheet (A-shares: AShareBalanceFetcher;
    tot_share_equity_incl_min_int -> 股东权益 (identity verified).
    HK: default provider).
    """
    from mysharelib.tools import normalize_symbol
    from . import provider as _provider

    symbol_b, symbol_f, market = normalize_symbol(ticker)
    if market in _AMAZINGDATA_MARKETS:
        df = _a_share_fetch(_provider.AShareBalanceFetcher, symbol_f, period, limit)
        return df[["period_ending", "fiscal_period", "股东权益", "总负债", "总资产"]]
    balance_df = obb.equity.fundamental.balance(symbol=symbol_b, period=period, limit=limit, provider=default_provider).to_dataframe().head(limit)
    if market  == "HK":
        if "股东权益合计" in balance_df.columns:
            return balance_df[["period_ending", "股东权益合计", "总负债", "总资产"]]
        else:
            return balance_df[["period_ending", "总权益", "总负债", "总资产"]]
    else:
        return balance_df[["period_ending", "fiscal_period", "股东权益", "总负债", "总资产"]]

def get_cash_flow(ticker: str, period: str, limit: int) -> pd.DataFrame:
    """
    Get cash flow (A-shares: AShareCashFetcher; HK: default provider).
    """
    from mysharelib.tools import normalize_symbol
    from . import provider as _provider

    symbol_b, symbol_f, market = normalize_symbol(ticker)
    if market in _AMAZINGDATA_MARKETS:
        df = _a_share_fetch(_provider.AShareCashFetcher, symbol_f, period, limit)
        return df[["period_ending", "fiscal_period", "营业性现金流", "投资性现金流", "融资性现金流"]]
    cash_flow_df = obb.equity.fundamental.cash(symbol=symbol_b, period=period, limit=limit, provider=default_provider).to_dataframe().head(limit)
    if market  == "HK":
        return cash_flow_df
    else:
        return cash_flow_df[["period_ending", "fiscal_period","营业性现金流","投资性现金流","融资性现金流"]]

def get_income(ticker: str, period: str, limit: int) -> pd.DataFrame:
    """
    Get income statement (A-shares: AShareIncomeFetcher;
    tot_opera_rev -> 总营收, net_pro_excl_min_int_inc -> 净利润(归母).
    HK: default provider).
    """
    from mysharelib.tools import normalize_symbol
    from . import provider as _provider

    symbol_b, symbol_f, market = normalize_symbol(ticker)
    if market in _AMAZINGDATA_MARKETS:
        df = _a_share_fetch(_provider.AShareIncomeFetcher, symbol_f, period, limit)
        return df[["period_ending", "fiscal_period", "总营收", "营业利润", "净利润", "基本每股收益"]]

    income_df = obb.equity.fundamental.income(symbol=symbol_b, period=period, limit=limit, provider=default_provider).to_dataframe()
    if market  == "HK":
        if "经营收入总额" in income_df.columns:
            return income_df[["period_ending",'经营收入总额','股东应占溢利']].head(limit)
        else:
            return income_df[["period_ending",'营业额','股东应占溢利']].head(limit)
    else:
        if "总营收" in income_df.columns:
        # Column exists
            return income_df[["period_ending","fiscal_period","总营收","净利润"]].head(limit)
        elif "OPERATE_INCOME" in income_df.columns:
            new_df = income_df[["period_ending","fiscal_period","OPERATE_INCOME","净利润"]]
            new_df = new_df.rename(columns={"OPERATE_INCOME": "总营收"})
            return new_df.head(limit)
        else:
            raise ValueError("Neither '总营收' nor 'OPERATE_INCOME' found in the DataFrame columns.")
