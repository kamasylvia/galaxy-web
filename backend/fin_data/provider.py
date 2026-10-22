"""AmazingData DB-backed fetchers for galaxy-web widgets (W4 provider regularization).

Each fetcher implements the OpenBB ``Fetcher`` interface
(transform_query / extract_data / transform_data) against local
TimescaleDB via ``fin_data._db``. Data models mirror the akshare
plugin's Chinese-field convention (same widget contract), with
``__alias_dict__`` pointing at galaxy-core English columns.

This is the G3 fetcher set in thin local form. When Workspace needs
``obb``-router consumption, register these in a provider package
(the vendor dir already holds the EquityHistorical precedent).
"""

import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.balance_sheet import (
    BalanceSheetData,
    BalanceSheetQueryParams,
)
from openbb_core.provider.standard_models.cash_flow import (
    CashFlowStatementData,
    CashFlowStatementQueryParams,
)
from openbb_core.provider.standard_models.equity_historical import (
    EquityHistoricalData,
    EquityHistoricalQueryParams,
)
from openbb_core.provider.standard_models.income_statement import (
    IncomeStatementData,
    IncomeStatementQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import Field

from . import _db


def _rows(table: str, symbol: str, period: str | None, limit: int | None) -> list[dict]:
    symbols = [symbol] if isinstance(symbol, str) else symbol
    out: list[dict] = []
    for s in symbols:
        df = _db.fetch_statements(table, s, period or "annual", limit or 5)
        out.extend(df.to_dict(orient="records"))
    if not out:
        raise EmptyDataError()
    return out


# --- K-line (delegates to the vendored EquityHistorical fetcher) ---

class AShareHistoricalFetcher(Fetcher[EquityHistoricalQueryParams, list[EquityHistoricalData]]):
    """K-line fetcher: delegates to the vendored AmazingData fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> EquityHistoricalQueryParams:
        return EquityHistoricalQueryParams(**params)

    @staticmethod
    def extract_data(
        query: EquityHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        from openbb_provider_amazingdata.models.equity_historical import (
            AmazingDataEquityHistoricalFetcher as _Vendored,
        )

        vq = _Vendored.transform_query(query.model_dump(mode="json"))
        return _Vendored.extract_data(vq, credentials)

    @staticmethod
    def transform_data(
        query: EquityHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[EquityHistoricalData]:
        return [EquityHistoricalData.model_validate(d) for d in data]


# --- Income ---

class AShareIncomeData(IncomeStatementData):
    """A-share income (same widget contract as the akshare plugin)."""

    __alias_dict__ = {
        "period_ending": "reporting_period",
        "fiscal_period": "statement_type",
        "总营收": "tot_opera_rev",
        "营业利润": "opera_profit",
        "净利润": "net_pro_excl_min_int_inc",
        "基本每股收益": "basic_eps",
    }

    总营收: Optional[float] = Field(default=None, description="总营收.")
    营业利润: Optional[float] = Field(default=None, description="营业利润.")
    净利润: Optional[float] = Field(default=None, description="净利润(归母).")
    基本每股收益: Optional[float] = Field(default=None, description="基本每股收益.")


class AShareIncomeFetcher(Fetcher[IncomeStatementQueryParams, list[AShareIncomeData]]):
    """Income from galaxy-core income table."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> IncomeStatementQueryParams:
        return IncomeStatementQueryParams(**params)

    @staticmethod
    def extract_data(
        query: IncomeStatementQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        return _rows("income", query.symbol, query.period, query.limit)

    @staticmethod
    def transform_data(
        query: IncomeStatementQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[AShareIncomeData]:
        return [AShareIncomeData.model_validate(d) for d in data]


# --- Balance ---

class AShareBalanceData(BalanceSheetData):
    """A-share balance (same widget contract as the akshare plugin)."""

    __alias_dict__ = {
        "period_ending": "reporting_period",
        "fiscal_period": "statement_type",
        "股东权益": "tot_share_equity_incl_min_int",
        "总负债": "total_liab",
        "总资产": "total_assets",
    }

    股东权益: Optional[float] = Field(default=None, description="股东权益(含少股).")
    总负债: Optional[float] = Field(default=None, description="总负债.")
    总资产: Optional[float] = Field(default=None, description="总资产.")


class AShareBalanceFetcher(Fetcher[BalanceSheetQueryParams, list[AShareBalanceData]]):
    """Balance from galaxy-core balance_sheet table."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> BalanceSheetQueryParams:
        return BalanceSheetQueryParams(**params)

    @staticmethod
    def extract_data(
        query: BalanceSheetQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        return _rows("balance_sheet", query.symbol, query.period, query.limit)

    @staticmethod
    def transform_data(
        query: BalanceSheetQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[AShareBalanceData]:
        return [AShareBalanceData.model_validate(d) for d in data]


# --- Cash flow ---

class AShareCashData(CashFlowStatementData):
    """A-share cash flow (same widget contract as the akshare plugin)."""

    __alias_dict__ = {
        "period_ending": "reporting_period",
        "fiscal_period": "statement_type",
        "营业性现金流": "net_cash_flows_opera_act",
        "投资性现金流": "net_cash_flows_inv_act",
        "融资性现金流": "net_cash_flows_fin_act",
    }

    营业性现金流: Optional[float] = Field(default=None, description="营业性现金流.")
    投资性现金流: Optional[float] = Field(default=None, description="投资性现金流.")
    融资性现金流: Optional[float] = Field(default=None, description="融资性现金流.")


class AShareCashFetcher(Fetcher[CashFlowStatementQueryParams, list[AShareCashData]]):
    """Cash flow from galaxy-core cash_flow table."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> CashFlowStatementQueryParams:
        return CashFlowStatementQueryParams(**params)

    @staticmethod
    def extract_data(
        query: CashFlowStatementQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        return _rows("cash_flow", query.symbol, query.period, query.limit)

    @staticmethod
    def transform_data(
        query: CashFlowStatementQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[AShareCashData]:
        return [AShareCashData.model_validate(d) for d in data]


# --- Profile (stock_basic; bespoke Data, no standard model fits) ---

class AShareProfileData(Data):
    """Company profile from stock_basic."""

    __alias_dict__ = {
        "symbol": "symbol",
        "公司名称": "comp_name",
        "证券简称": "security_name",
        "上市日期": "list_date",
        "退市日期": "delist_date",
        "板块": "listplate_name",
        "在市": "is_listed",
    }

    symbol: str = Field(description="Symbol with suffix.")
    公司名称: Optional[str] = Field(default=None, description="公司名称.")
    证券简称: Optional[str] = Field(default=None, description="证券简称.")
    上市日期: Any = Field(default=None, description="上市日期.")
    退市日期: Any = Field(default=None, description="退市日期.")
    板块: Optional[str] = Field(default=None, description="板块.")
    在市: Optional[bool] = Field(default=None, description="在市.")


class AShareProfileFetcher(Fetcher[dict, list[AShareProfileData]]):
    """Profile from stock_basic (single symbol, no QueryParams)."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> dict:
        return params

    @staticmethod
    def extract_data(
        query: dict,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        return _db.fetch_profile(query["symbol"]).to_dict(orient="records")

    @staticmethod
    def transform_data(
        query: dict,
        data: list[dict],
        **kwargs: Any,
    ) -> list[AShareProfileData]:
        out = []
        for d in data:
            out.append(AShareProfileData.model_validate({
                "symbol": d.get("symbol"),
                "comp_name": d.get("公司名称"),
                "security_name": d.get("证券简称"),
                "list_date": d.get("上市日期"),
                "delist_date": d.get("退市日期"),
                "listplate_name": d.get("板块"),
                "is_listed": d.get("在市"),
            }))
        return out
