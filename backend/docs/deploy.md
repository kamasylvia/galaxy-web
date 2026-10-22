# galaxy-web 部署指南(双轨:Docker / NixOS 原生)

> 两种方式二选一,行为一致(监听 0.0.0.0:8000,24 widgets)。
> 前置:PostgreSQL/TimescaleDB `galaxy` 库可达(含 `obb_equity_historical`
> 视图与 W2/W3 业务表);A 股 widgets 只读本地库,HK/实时链走 akshare。

## 共同配置

```bash
cp .env.example .env   # 填 APP_API_KEY + GALAXY_PG_* (见下)
```

| 变量 | 含义 | 默认 |
|---|---|---|
| `APP_API_KEY` | Workspace 后端鉴权 key | 必填 |
| `GALAXY_PG_HOST` | PG 主机 | `127.0.0.1`(原生) |
| `GALAXY_PG_PORT` | PG 端口 | `5432` |
| `GALAXY_PG_DB/USER/PASSWORD` | 库/用户/密码 | `galaxy/postgres/postgres` |
| `OPENROUTER_API_KEY` | AI 链(暂未用,占位) | 可空 |

## Docker

```bash
docker build -t galaxy-web:latest .
docker compose up -d
curl http://127.0.0.1:8000/health
```

- `GALAXY_PG_HOST`:容器内 `127.0.0.1` 指向容器自身;宿主 PG 用
  `host.docker.internal`(compose 已默认),LAN/QNAP PG 直接填 IP/Tailscale 名。
- akshare 凭据(HK/实时链需要;纯 A 股可跳过):
  建 `user_settings.json`(`{"credentials":{"akshare_api_key":"..."}}`),
  compose 已挂载为只读 `/root/.openbb_platform/user_settings.json`。

## NixOS 原生

module: `nixos-config/modules/services/galaxy-web.nix`
(systemd user service,仿 alphamaster-web)。

```bash
# 1. 敏感项落盘(不进 nix store):
cat > ~/.config/galaxy-web.env <<'EOF'
APP_API_KEY=<...>
GALAXY_PG_HOST=127.0.0.1
GALAXY_PG_PORT=5432
GALAXY_PG_DB=galaxy
GALAXY_PG_USER=postgres
GALAXY_PG_PASSWORD=postgres
OPENROUTER_API_KEY=<...>
EOF
chmod 600 ~/.config/galaxy-web.env

# 2. rebuild + 起服务:
sudo nixos-rebuild switch --flake ~/nixos-config#lenovo
systemctl --user daemon-reload
systemctl --user enable --now galaxy-web
journalctl --user -u galaxy-web -f
```

- 防火墙:放行 8000(参考 alphamaster-web 的 8765 条目)。
- akshare 凭据(同上,纯 A 股可跳过):
  `~/.openbb_platform/user_settings.json`。
- 本地开发等价命令:`uv run uvicorn main:app --reload`(3.12 venv)。

## Workspace 联调

OpenBB Workspace → Add Backend → URL 填
`http://<host>:8000`(LAN 用宿主 IP/Tailscale 名) →
出现 **A股** app → 三模块出数(Profile/Financials/Stock Price)。
