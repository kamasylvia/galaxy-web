"""Minimal /v1/dashboard CRUD for the Finanalyzer frontend.

The Finanalyzer app (open-source Workspace) persists user dashboards via
its api backend (`/v1/dashboard`). Instead of deploying finanalyzer/api,
this backend implements the same contract with JSON-file persistence
(`data/dashboards.json`, honoring DATA_FOLDER_PATH). Same auth as the
rest of the app (Bearer APP_API_KEY).
"""

import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_current_user

dashboard_router = APIRouter()

_DATA_DIR = Path(os.getenv("DATA_FOLDER_PATH", "data"))
_STORE = _DATA_DIR / "dashboards.json"


def _load() -> dict[str, dict[str, Any]]:
    if not _STORE.exists():
        return {}
    try:
        data = json.loads(_STORE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save(store: dict[str, dict[str, Any]]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


class DashboardIn(BaseModel):
    id: str | None = None
    name: str = "Untitled"
    description: str | None = None
    widgets: list[dict[str, Any]] = []
    tabs: list[dict[str, Any]] | None = None
    groups: list[dict[str, Any]] | None = None


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    widgets: list[dict[str, Any]] | None = None
    tabs: list[dict[str, Any]] | None = None
    groups: list[dict[str, Any]] | None = None


class WidgetIn(BaseModel):
    id: str | None = None
    type: str = "table"
    title: str = ""
    position: dict[str, Any] = {}
    data: dict[str, Any] | None = None


@dashboard_router.get("/dashboard")
def list_dashboards(token: str = Depends(get_current_user)):
    """List all dashboards."""
    return list(_load().values())


@dashboard_router.post("/dashboard")
def create_dashboard(body: DashboardIn, token: str = Depends(get_current_user)):
    """Create a dashboard (server assigns id if absent)."""
    store = _load()
    dash_id = body.id or f"dash-{uuid.uuid4().hex[:8]}"
    dash = body.model_dump()
    dash["id"] = dash_id
    store[dash_id] = dash
    _save(store)
    return dash


@dashboard_router.get("/dashboard/{dash_id}")
def get_dashboard(dash_id: str, token: str = Depends(get_current_user)):
    """Get one dashboard."""
    dash = _load().get(dash_id)
    if dash is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dash


@dashboard_router.put("/dashboard/{dash_id}")
def update_dashboard(dash_id: str, body: DashboardUpdate, token: str = Depends(get_current_user)):
    """Update dashboard fields (only provided keys)."""
    store = _load()
    dash = store.get(dash_id)
    if dash is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        dash[k] = v
    store[dash_id] = dash
    _save(store)
    return dash


@dashboard_router.delete("/dashboard/{dash_id}", status_code=204)
def delete_dashboard(dash_id: str, token: str = Depends(get_current_user)):
    """Delete a dashboard."""
    store = _load()
    if dash_id not in store:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    del store[dash_id]
    _save(store)
    return None


@dashboard_router.post("/dashboard/{dash_id}/widgets")
def add_widget(dash_id: str, body: WidgetIn, token: str = Depends(get_current_user)):
    """Append a widget to a dashboard."""
    store = _load()
    dash = store.get(dash_id)
    if dash is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    widget = body.model_dump()
    widget["id"] = widget.get("id") or f"w-{uuid.uuid4().hex[:8]}"
    dash.setdefault("widgets", []).append(widget)
    store[dash_id] = dash
    _save(store)
    return widget


@dashboard_router.put("/dashboard/{dash_id}/widgets/{widget_id}")
def update_widget(
    dash_id: str, widget_id: str, body: dict[str, Any], token: str = Depends(get_current_user)
):
    """Update one widget in place."""
    store = _load()
    dash = store.get(dash_id)
    if dash is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    for i, w in enumerate(dash.get("widgets", [])):
        if w.get("id") == widget_id:
            w.update(body)
            w["id"] = widget_id
            dash["widgets"][i] = w
            store[dash_id] = dash
            _save(store)
            return w
    raise HTTPException(status_code=404, detail="Widget not found")


@dashboard_router.delete("/dashboard/{dash_id}/widgets/{widget_id}", status_code=204)
def delete_widget(dash_id: str, widget_id: str, token: str = Depends(get_current_user)):
    """Remove one widget."""
    store = _load()
    dash = store.get(dash_id)
    if dash is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    widgets = [w for w in dash.get("widgets", []) if w.get("id") != widget_id]
    if len(widgets) == len(dash.get("widgets", [])):
        raise HTTPException(status_code=404, detail="Widget not found")
    dash["widgets"] = widgets
    store[dash_id] = dash
    _save(store)
    return None
