# 03 — 终端代理豁免（仅特殊网络环境需要）

> 通用环境（本机直连后端）跳过本节。只有终端开代理、且后端走内网域名/IP 时才需要。

## 问题

终端开着代理（如 `http_proxy=http://127.0.0.1:10809`）时，发往内网后端（如 tailscale 域名、局域网 IP）的请求会被塞进代理黑洞：ping 通但 HTTP 全超时。

## 解法

`NO_PROXY`（大小写都要有，curl 只认小写）必须含内网直连项，示例（tailscale 场景）：

```
localhost,127.0.0.1,::1,.local,<内网域名>,<内网网段>
```

生效步骤（新 shell 做一次）：

```bash
source ~/.config/xray/proxy.bash   # 或你环境的代理 env 文件
export no_proxy="$NO_PROXY" noProxy="$NO_PROXY"
curl -s -m5 -o /dev/null -w "%{http_code}\n" http://<backend-host>:<port>/api/v1/health  # 应 200
```

模板改完需重启代理 daemon 再生 env 文件（以 xray 为例：先 stop 再 start，复用旧 daemon 不重生 env）。

## 诊断

```bash
curl -s -m5 -v http://<backend-host>:<port>/api/v1/health -o /dev/null 2>&1 | grep -E "Trying|Connected"
# Trying <内网IP>:<port> → 直连，正常
# Trying 127.0.0.1:10809   → 还在走代理，检查 NO_PROXY/no_proxy
nc -z <backend-ip> <port> && echo TCP-OK   # TCP 通但 HTTP 超时 = 后端 hang，非代理问题
```
