# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Local API and web app: `python -m ejariflow.server` then open http://127.0.0.1:8770.

Standard library only. It listens on localhost and refuses requests whose Host or Origin belongs to
another site, so a web page you visit can't use it to read your contracts.
"""

import argparse
import datetime as dt
import http.server
import json
import pathlib
import urllib.parse
from typing import Any, Dict, Tuple

from . import rera
from .audit import audit_contract
from .contract import parse_contract
from .notice import generate_90day_notice
from .portfolio import analyse, load_sample

WEB = pathlib.Path(__file__).resolve().parent.parent / "web"
MAX_BODY = 2_000_000
LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]"}


def _num(p: Dict[str, Any], key: str) -> float:
    try:
        return float(p[key])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"'{key}' must be a number.")


def route(method: str, path: str, p: Dict[str, Any]) -> Tuple[int, Any]:
    if method == "GET" and path == "/api/portfolio":
        return 200, analyse(load_sample())
    if method == "POST" and path == "/api/rera/check":
        return 200, rera.check_increase(_num(p, "current_rent"), _num(p, "proposed_rent"), _num(p, "average_rent"))
    if method == "POST" and path in ("/api/contract/parse", "/api/contract/audit"):
        text = str(p.get("text") or "")
        if not text.strip():
            raise ValueError("Paste the contract text first.")
        contract = parse_contract(text)
        if path.endswith("parse"):
            return 200, contract
        avg = float(p["average_rent"]) if p.get("average_rent") not in (None, "") else None
        return 200, {"contract": contract, "audit": audit_contract(contract, average_rent=avg)}
    if method == "POST" and path == "/api/notice/generate":
        notice = generate_90day_notice(
            tenant=str(p.get("tenant") or "Tenant"),
            landlord=str(p.get("landlord") or "Landlord"),
            property_name=str(p.get("property_name") or "Property"),
            unit=str(p.get("unit") or "101"),
            area=str(p.get("area") or "Dubai"),
            current_rent=_num(p, "current_rent"),
            average_rent=_num(p, "average_rent"),
            lease_end_date=str(p.get("lease_end_date") or dt.date.today().isoformat()),
            notice_date=p.get("notice_date"),
            proposed_rent=float(p["proposed_rent"]) if p.get("proposed_rent") not in (None, "") else None,
            ejari_number=p.get("ejari_number"),
            cheques=int(p.get("cheques") or 4),
        )
        return 200, notice
    return 404, {"error": "Not found"}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "EjariFlow"

    def log_message(self, *args):
        pass

    def _local(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0] if not (self.headers.get("Host") or "").startswith("[") else (self.headers.get("Host") or "").split("]")[0] + "]"
        if host not in LOCAL_HOSTS:
            return False
        origin = self.headers.get("Origin")
        if origin:
            o = urllib.parse.urlsplit(origin)
            return o.hostname in ("127.0.0.1", "localhost", "::1") and o.port == self.server.server_address[1]
        return True

    def _send(self, status: int, body: Any, ctype: str = "application/json") -> None:
        data = json.dumps(body).encode() if ctype == "application/json" else body
        self.send_response(status)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith(("text/", "application/json")) else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _handle(self, method: str) -> None:
        if not self._local():
            self._send(403, {"error": "Requests from other sites are refused."})
            return
        path = urllib.parse.urlsplit(self.path).path
        if method == "GET" and not path.startswith("/api/"):
            name = "index.html" if path in ("/", "") else path.lstrip("/")
            target = (WEB / name).resolve()
            if WEB not in target.parents or not target.is_file():
                self._send(404, {"error": "Not found"})
                return
            ctype = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json"}.get(target.suffix, "application/octet-stream")
            self._send(200, target.read_bytes(), ctype)
            return
        payload: Dict[str, Any] = {}
        if method == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                self._send(413, {"error": "Too large."})
                return
            try:
                payload = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                self._send(400, {"error": "Body must be JSON."})
                return
        try:
            status, body = route(method, path, payload if isinstance(payload, dict) else {})
        except ValueError as e:
            status, body = 400, {"error": str(e)}
        self._send(status, body)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


def make_server(host: str = "127.0.0.1", port: int = 8770) -> http.server.ThreadingHTTPServer:
    return http.server.ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    ap = argparse.ArgumentParser(description="EjariFlow AI local server")
    ap.add_argument("--port", type=int, default=8770)
    args = ap.parse_args()
    srv = make_server("127.0.0.1", args.port)
    print(f"EjariFlow AI running at http://127.0.0.1:{args.port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
