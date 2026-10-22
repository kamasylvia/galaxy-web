from fastapi import APIRouter, HTTPException
import plotly.graph_objects as go
import pandas as pd
from typing import List
import json
import asyncio
import numpy as np
from openbb import obb
from core.registry import register_widget
from core.plotly_config import (
    apply_config_to_figure, 
    get_chart_colors,
    create_base_layout
)

charts_router = APIRouter()

def get_chart_data(
    ticker: str,
    interval: str,
    interval_multiplier: int,
    start_date: str,
    end_date: str
) -> dict:
    from mysharelib.tools import normalize_symbol, get_valid_date
    from fin_data.profile import _amazingdata_prices

    _, symbol_f, market = normalize_symbol(ticker)
    start_dt = get_valid_date(start_date)
    end_dt = get_valid_date(end_date)
    if market in ("SH", "SZ", "BJ"):
        data = _amazingdata_prices(symbol_f, str(start_dt), str(end_dt))
    else:
        data = obb.equity.price.historical(symbol=ticker, start_date=start_dt, end_date=end_dt, provider="akshare").to_dataframe()
    theme: str = "dark"
    # Get chart colors based on theme
    colors = get_chart_colors(theme)

    figure = go.Figure(
        layout=create_base_layout(
            x_title="Date",
            y_title="Price",
            y_dtype="$,.4f",
            theme=theme
        )
    )
    # Add candlestick chart second so it appears on top
    figure.add_candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name="Price",
        increasing_line_color=colors['positive'],
        decreasing_line_color=colors['negative']
    )
    # Update layout to include secondary y-axis for volume
    figure.update_layout(
        yaxis=dict(
            rangemode="nonnegative",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="lightgrey"
        ),
    )
    # Apply the standard configuration to the figure with theme
    figure = apply_config_to_figure(figure, theme=theme)

    # Convert figure to JSON with the config
    figure_json = figure.to_json()
    figure_dict = json.loads(figure_json)
    
    return figure_dict
