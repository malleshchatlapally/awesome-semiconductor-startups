"""Minimal HTTP server for iPhone Shortcuts heartbeats."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from iphone_state import IPhoneState


def _authorized(headers: BaseHTTPRequestHandler, secret: str) -> bool:
    if not secret:
        return True
    auth = headers.headers.get("Authorization", "")
    if auth == f"Bearer {secret}":
        return True
    token = headers.headers.get("X-Agent-Token", "")
    return token == secret


class _Handler(BaseHTTPRequestHandler):
    state: IPhoneState
    secret: str

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_json(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in ("/v1/heartbeat", "/v1/tick"):
            self._send_json(404, {"error": "not found"})
            return
        if not _authorized(self, self.secret):
            self._send_json(401, {"error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)

        self.state.record_heartbeat()
        extra = self.state.pop_pending_alert() or {}
        self._send_json(200, {"ok": True, **extra})


def start_iphone_server(
    state: IPhoneState,
    host: str,
    port: int,
    secret: str,
) -> ThreadingHTTPServer:
    handler = type(
        "IPhoneHandler",
        (_Handler,),
        {"state": state, "secret": secret},
    )
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

