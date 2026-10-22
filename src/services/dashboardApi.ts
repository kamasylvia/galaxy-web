import { getAuthHeaders, getAuthQueryParams, handleUnauthorized } from "./authService";
import { connectionService } from "./connections/connectionService";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// Prefer the user's connected backend URL (runtime "connection" page)
// over the build-time default, so LAN/Tailscale/remote entries all work.
function resolveBaseUrl(): string {
  try {
    const conns = connectionService.getConnections();
    const active = conns.find((c) => c.status === "connected" && c.url);
    if (active) {
      return active.url.endsWith("/") ? active.url.slice(0, -1) : active.url;
    }
  } catch {
    // localStorage unavailable (SSR/tests) -> fall through to build default
  }
  return API_BASE_URL;
}

function buildUrl(path: string): string {
  const base = resolveBaseUrl();
  if (!base) {
    return path;
  }

  const basePath = `${base}${path}`;
  const authParams = getAuthQueryParams(resolveBaseUrl());
  const queryString = authParams.toString();

  return queryString ? `${basePath}?${queryString}` : basePath;
}

export interface Widget {
  id: string;
  type: string;
  title: string;
  position: Record<string, unknown>;
  data?: Record<string, unknown>;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widgets: Widget[];
  created_at?: string;
  updated_at?: string;
  tabs?: Array<{ id: string; name: string; icon?: string }>;
  groups?: Array<{
    name: string;
    type: string;
    paramName: string;
    defaultValue: string | number | boolean;
    widgetIds: string[];
  }>;
}

export interface DashboardCreate {
  id: string;
  name: string;
  description?: string;
  widgets?: Widget[];
  tabs?: Array<{ id: string; name: string; icon?: string }>;
  groups?: Array<{
    name: string;
    type: string;
    paramName: string;
    defaultValue: string | number | boolean;
    widgetIds: string[];
  }>;
}

export interface DashboardUpdate {
  name?: string;
  description?: string;
  widgets?: Widget[];
  tabs?: Array<{ id: string; name: string; icon?: string }>;
  groups?: Array<{
    name: string;
    type: string;
    paramName: string;
    defaultValue: string | number | boolean;
    widgetIds: string[];
  }>;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      handleUnauthorized();
    }
    
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Response body is not JSON, use status text
    }
    throw new Error(`Dashboard API error (${response.status}): ${detail}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export async function getDashboards(): Promise<Dashboard[]> {
  const response = await fetch(buildUrl("/v1/dashboard"), {
    headers: getAuthHeaders(resolveBaseUrl()),
  });
  return handleResponse<Dashboard[]>(response);
}

export async function getDashboard(id: string): Promise<Dashboard> {
  const response = await fetch(buildUrl(`/v1/dashboard/${id}`), {
    headers: getAuthHeaders(resolveBaseUrl()),
  });
  return handleResponse<Dashboard>(response);
}

export async function createDashboard(data: DashboardCreate): Promise<Dashboard> {
  const response = await fetch(buildUrl("/v1/dashboard"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders(resolveBaseUrl()) },
    body: JSON.stringify(data),
  });
  return handleResponse<Dashboard>(response);
}

export async function updateDashboard(
  id: string,
  data: DashboardUpdate,
): Promise<Dashboard> {
  const response = await fetch(buildUrl(`/v1/dashboard/${id}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...getAuthHeaders(resolveBaseUrl()) },
    body: JSON.stringify(data),
  });
  return handleResponse<Dashboard>(response);
}

export async function deleteDashboard(id: string): Promise<void> {
  const response = await fetch(buildUrl(`/v1/dashboard/${id}`), {
    method: "DELETE",
    headers: getAuthHeaders(resolveBaseUrl()),
  });
  return handleResponse<void>(response);
}

export async function addWidget(
  dashboardId: string,
  widget: Widget,
): Promise<Widget> {
  const response = await fetch(buildUrl(`/v1/dashboard/${dashboardId}/widgets`), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders(resolveBaseUrl()) },
    body: JSON.stringify(widget),
  });
  return handleResponse<Widget>(response);
}

export async function updateWidget(
  dashboardId: string,
  widgetId: string,
  data: Partial<Widget>,
): Promise<Widget> {
  const response = await fetch(
    buildUrl(`/v1/dashboard/${dashboardId}/widgets/${encodeURIComponent(widgetId)}`),
    {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...getAuthHeaders(resolveBaseUrl()) },
      body: JSON.stringify(data),
    },
  );
  return handleResponse<Widget>(response);
}

export async function deleteWidget(
  dashboardId: string,
  widgetId: string,
): Promise<void> {
  const response = await fetch(
    buildUrl(`/v1/dashboard/${dashboardId}/widgets/${encodeURIComponent(widgetId)}`),
    { method: "DELETE", headers: getAuthHeaders(resolveBaseUrl()) },
  );
  return handleResponse<void>(response);
}
