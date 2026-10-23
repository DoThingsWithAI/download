# download

在 Linux / Ubuntu 服务器上临时共享**指定的一个 ZIP 文件**，使用浏览器将它下载到自己的电脑。

脚本只服务你明确指定的文件，不提供目录列表，不允许通过 URL 选择服务器上的其他文件。

## 1. 在服务器上安装脚本

```bash
curl -fsSL https://raw.githubusercontent.com/DoThingsWithAI/download/main/download_server.py \
  -o /tmp/download_server.py
```

## 2. 安全方式（推荐：不开放公网端口）

在服务器上运行：

```bash
python3 /tmp/download_server.py /opt/backups/example.zip
```

它会打印固定地址 `http://127.0.0.1:8765/download`（运行期间保持这个终端打开）。

在你**自己的电脑**上另开终端，建立 SSH 隧道：

```bash
ssh -N -L 8765:127.0.0.1:8765 用户名@服务器公网IP
```

然后在本机浏览器打开 `http://127.0.0.1:8765/download` 即可下载。

## 3. 直接使用服务器 IP 下载（不推荐在公网使用 HTTP）

```bash
python3 /tmp/download_server.py /opt/backups/example.zip --public
```

脚本打印：

```text
http://<服务器公网IP>:8765/download
```

把其中的 `<服务器公网IP>` 改成你的实际公网 IP，再在浏览器打开。该方式需要服务器防火墙允许 TCP 8765 入站，并且 **HTTP 不加密**：任何能访问此地址的人均可下载该文件，且网络中间人可能窃听文件内容。建议使用上面的 SSH 隧道，或者通过已有的 HTTPS 反向代理访问。

## 参数

```bash
python3 /tmp/download_server.py <文件.zip> [--port 8765] [--ttl 900] [--public]
```

- 默认仅监听 `127.0.0.1:8765`。
- `--ttl` 控制最长运行秒数，默认 900 秒（15 分钟），最大 86400 秒。
- `--public` 监听 `0.0.0.0`，允许外部网络访问（若网络和防火墙允许）。
- 使用固定下载路径 `/download`，不生成随机令牌。
- 完整发送一次 ZIP 后，服务自动退出；在规定时间内也可按 Ctrl+C 停止。
- 下载异常中断时，有效期内可重试。
- 支持大文件流式传输，不一次读入内存。
- Python 3.8+，无需额外 pip 安装。

**提示**：服务按你指定的路径读取文件，运行脚本的系统用户必须有该文件的读取权限。**公开监听时不需要任何认证，建议只短时使用并通过防火墙限制访问源 IP。**
