"""Temporary HTTPS upload receiver for the one-time Render preview restore.

Run only on the preview API service before switching its start command to
uvicorn. Render terminates HTTPS and forwards the request to this HTTP server.
The uploaded SQL archive must match the locally verified backup conversion.
"""

import gzip
import hashlib
import json
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


EXPECTED_SHA256 = "6219c30e3aafa1fee75a1873334d86718e902b562bad84d0d52f7d00b4e24559"
EXPECTED_SIZE = 5_167_799
state = {"status": "waiting"}
lock = threading.Lock()


def pg_environment():
    url = urlsplit(os.environ["DATABASE_URL"])
    if url.scheme not in ("postgres", "postgresql") or not url.hostname:
        raise ValueError("DATABASE_URL must be a PostgreSQL URL")
    env = os.environ.copy()
    env.update(
        PGHOST=url.hostname,
        PGPORT=str(url.port or 5432),
        PGUSER=unquote(url.username or ""),
        PGPASSWORD=unquote(url.password or ""),
        PGDATABASE=unquote(url.path.lstrip("/")),
        PGSSLMODE="require",
        PGCONNECT_TIMEOUT="15",
    )
    return env


def run_psql(env, *args):
    result = subprocess.run(
        ["psql", "-X", "-v", "ON_ERROR_STOP=1", *args],
        env=env,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"psql failed with exit code {result.returncode}: {result.stderr[-600:]}")
    return result.stdout.strip()


def table_count(env):
    return int(run_psql(env, "-t", "-A", "-c", "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"))


def restore(archive_path):
    sql_path = archive_path.with_suffix(".sql")
    try:
        env = pg_environment()
        if table_count(env) != 0:
            raise RuntimeError("Database is not empty; restore was cancelled")
        with gzip.open(archive_path, "rb") as compressed, sql_path.open("wb") as plain:
            while chunk := compressed.read(1024 * 1024):
                plain.write(chunk)
        run_psql(env, "-1", "-f", str(sql_path))
        counts = run_psql(env, "-t", "-A", "-F", ",", "-c", "SELECT (SELECT count(*) FROM public.hospitals), (SELECT count(*) FROM public.hospital_measures), (SELECT count(*) FROM public.hospital_directory_entries)")
        with lock:
            state.update(status="done", counts=counts)
    except Exception as exc:
        with lock:
            state.update(status="failed", error=str(exc))
    finally:
        archive_path.unlink(missing_ok=True)
        sql_path.unlink(missing_ok=True)


class Handler(BaseHTTPRequestHandler):
    def respond(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path not in ("/health", "/status"):
            return self.respond(404, {"error": "not found"})
        with lock:
            return self.respond(200, dict(state))

    def do_POST(self):
        if self.path != "/restore":
            return self.respond(404, {"error": "not found"})
        with lock:
            if state["status"] not in ("waiting", "failed"):
                return self.respond(409, {"error": "restore already started"})
            state.clear()
            state["status"] = "receiving"
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size != EXPECTED_SIZE:
                raise ValueError("Wrong backup size")
            fd, temp_name = tempfile.mkstemp(prefix="carecompass-restore-", suffix=".gz")
            archive_path = Path(temp_name)
            digest = hashlib.sha256()
            with os.fdopen(fd, "wb") as stream:
                remaining = size
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError("Incomplete upload")
                    stream.write(chunk)
                    digest.update(chunk)
                    remaining -= len(chunk)
            if digest.hexdigest() != EXPECTED_SHA256:
                raise ValueError("Backup checksum mismatch")
            with lock:
                state["status"] = "restoring"
            threading.Thread(target=restore, args=(archive_path,), daemon=True).start()
            return self.respond(202, {"status": "restoring"})
        except Exception as exc:
            if "archive_path" in locals():
                archive_path.unlink(missing_ok=True)
            with lock:
                state.update(status="failed", error=str(exc))
            return self.respond(400, {"error": str(exc)})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "10000"))), Handler).serve_forever()
