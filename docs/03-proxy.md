# 03 — 终端代理与 tailscale 豁免

## 问题

终端开着 xray 代理（`http_proxy=http://127.0.0.1:10809`）时，`lenovo:8000`（`100.100.193.74`，tailscale `100.64.0.0/10`）会被塞进代理黑洞：ping 通但 HTTP 全超时。

## 解法

`NO_PROXY` 必须含 tailscale 直连项。当前正本：

```
localhost,127.0.0.1,::1,.local,tailscale.com,controlplane.tailscale.com,.ts.net,elf-balance.ts.net,lenovo,100.64.0.0/10
```

生效步骤（新 shell 都要做一次）：

```bash
source ~/.config/xray/proxy.bash
export no_proxy="$NO_PROXY" noProxy="$NO_PROXY"   # 小写也要有，curl 只认小写
curl -s -m5 -o /dev/null -w "%{http_code}\n" http://lenovo:8000/health  # 应 200
```

## 模板位置（三地镜像，保持一致）

`NO_PROXY_HOSTS` / `NO_PROXY=` 共 6 处（每地 `xray.py` + `xray.sh` 各 2 模板 + 1 一次性 env）：

- `~/Documents/agents/scripts/xray.{py,sh}`
- vault 镜像 `03-Workspace/agents/scripts/xray.{py,sh}`
- QSync 镜像对应 `xray.{py,sh}`

改完重启 daemon 再生 `~/.config/xray/proxy.bash`：`px --stop && px --start`（`--start` 复用旧 daemon 不重生 env，必须先 stop）。

## 诊断

```bash
curl -s -m5 -v http://lenovo:8000/health -o /dev/null 2>&1 | grep -E "Trying|Connected"
# Trying 100.100.193.74:8000 → 直连，正常
# Trying 127.0.0.1:10809   → 还在走代理，检查 NO_PROXY/no_proxy
nc -z -G 3 100.100.193.74 8000 && echo TCP-OK   # TCP 通但 HTTP 超时 = 后端 hang，非代理问题
```
