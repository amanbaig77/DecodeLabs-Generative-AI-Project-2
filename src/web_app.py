from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.config import Settings
from src.generator import CopyGenerator
from src.models import CopyRequest

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"

HOST = "127.0.0.1"
PORT = 8000


class Handler(BaseHTTPRequestHandler):

    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict):
        self._send(
            status,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/health":
            self._json(
                200,
                {
                    "success": True,
                    "message": "Copywriting API is running."
                },
            )
            return

        if path == "/":
            file_path = FRONTEND / "index.html"

        elif path in {"/style.css", "/app.js"}:
            file_path = FRONTEND / path.lstrip("/")

        else:
            self._json(
                404,
                {
                    "success": False,
                    "error": "Not found"
                },
            )
            return

        if not file_path.exists():
            self._json(
                404,
                {
                    "success": False,
                    "error": f"Missing file: {file_path.name}"
                },
            )
            return

        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }.get(
            file_path.suffix,
            "application/octet-stream",
        )

        self._send(
            200,
            file_path.read_bytes(),
            content_type,
        )

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/api/generate":
            self._json(
                404,
                {
                    "success": False,
                    "error": "Not found"
                },
            )
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )

            raw = self.rfile.read(length)

            payload = json.loads(
                raw.decode("utf-8")
            )

            request = CopyRequest.model_validate(payload)

            settings = Settings.from_env()

            generator = CopyGenerator(settings)

            result = asyncio.run(
                generator.generate(request)
            )

            self._json(
                200,
                {
                    "success": True,
                    "data": result.model_dump(),
                },
            )

        except Exception as exc:
            self._json(
                400,
                {
                    "success": False,
                    "error": str(exc),
                },
            )

    def log_message(self, format, *args):
        print(
            f"[WEB] {self.address_string()} - "
            f"{format % args}"
        )


def main():

    FRONTEND.mkdir(
        exist_ok=True
    )

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    print("=" * 68)
    print(
        "DECODELABS - AUTOMATED "
        "COPYWRITING & TONE TRANSFORMER"
    )
    print(
        f"Web UI: http://{HOST}:{PORT}"
    )
    print(
        f"API:    http://{HOST}:{PORT}/api/generate"
    )
    print("Press Ctrl+C to stop.")
    print("=" * 68)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nServer stopped.")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()