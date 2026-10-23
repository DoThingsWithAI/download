#!/usr/bin/env python3
"""Serve one chosen ZIP file for a short time; no external dependencies."""

import argparse
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit


def main():
    parser = argparse.ArgumentParser(
        description="Temporarily download a server-side ZIP file from a browser."
    )
    parser.add_argument("zip_path", help="Absolute or relative path to an existing ZIP file")
    parser.add_argument("--port", type=int, default=8765, help="TCP port (default: 8765)")
    parser.add_argument("--ttl", type=int, default=900, help="Lifetime in seconds (default: 900)")
    parser.add_argument(
        "--public", action="store_true", help="Listen on all network interfaces (HTTP; use only on trusted networks or behind HTTPS)"
    )
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if not 1 <= args.ttl <= 86400:
        parser.error("--ttl must be between 1 and 86400")

    path = Path(args.zip_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".zip":
        parser.error("zip_path must point to an existing .zip file")
    try:
        with path.open("rb"):
            pass
    except OSError as exc:
        parser.error(f"cannot read file: {exc}")

    host = "0.0.0.0" if args.public else "127.0.0.1"

    class DownloadHandler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            # Suppress request logs.
            return

        def _send_headers(self, length):
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(length))
            self.send_header(
                "Content-Disposition",
                "attachment; filename=\"download.zip\"; filename*=UTF-8''" + quote(path.name),
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()

        def _handle(self, send_body):
            if urlsplit(self.path).path != "/download":
                self.send_error(404)
                return
            try:
                with path.open("rb") as source:
                    size = os.fstat(source.fileno()).st_size
                    self._send_headers(size)
                    if send_body:
                        while chunk := source.read(1024 * 1024):
                            self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                print("下载连接中断，链接在有效期内仍可重试。", flush=True)
                return
            except OSError as exc:
                print(f"读取或传输失败：{exc}", flush=True)
                return
            if send_body:
                print("文件已发送，正在关闭下载服务。", flush=True)
                threading.Thread(target=self.server.shutdown, daemon=True).start()

        def do_HEAD(self):
            self._handle(False)

        def do_GET(self):
            self._handle(True)

    try:
        server = ThreadingHTTPServer((host, args.port), DownloadHandler)
    except OSError as exc:
        parser.error(f"failed to listen on {host}:{args.port}: {exc}")

    route = "/download"
    print(f"提供文件：{path}", flush=True)
    print(f"有效时间：{args.ttl} 秒；下载成功后自动结束（Ctrl+C 可提前退出）", flush=True)
    if args.public:
        print(f"下载地址：http://<服务器公网IP>:{args.port}{route}", flush=True)
        print("警告：任何能访问这个地址的人都可以下载文件；公网 HTTP 不加密。建议优先使用 SSH 隧道。", flush=True)
    else:
        print(f"下载地址（SSH 隧道连接后，在本机浏览器打开）：http://127.0.0.1:{args.port}{route}", flush=True)
        print(f"本机建立隧道：ssh -N -L {args.port}:127.0.0.1:{args.port} 用户名@服务器IP", flush=True)

    timer = threading.Timer(args.ttl, server.shutdown)
    timer.daemon = True
    timer.start()
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("已手动停止。", flush=True)
    finally:
        timer.cancel()
        server.server_close()


if __name__ == "__main__":
    main()
