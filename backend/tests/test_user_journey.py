"""Run with: python -m pytest tests/test_user_journey.py -q

Uses a throwaway SQLite database, a Vite server, and installed Chrome or Edge.
Never connects to or refreshes the user's CareCompass database.
"""
import os
import socket
import subprocess
import sys
import time
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from datetime import date
from pathlib import Path
from urllib.request import urlopen

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.session import Base
from app.models.hospital import Hospital, HospitalQuality, Location, WaitTimeEstimate
from app.models.data import HospitalPresence

playwright = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

def wait_url(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise AssertionError(f"Server exited early: {url}")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200: return
        except Exception: time.sleep(.2)
    raise AssertionError(f"Server did not become ready: {url}")

@pytest.fixture(scope="module")
def app_servers(tmp_path_factory):
    chrome = next((path for path in (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ) if path.exists()), None)
    if not chrome: pytest.skip("Chrome or Edge is needed for browser journeys")
    if not (FRONTEND / "dist" / "index.html").exists(): pytest.skip("Build the frontend first: npm.cmd run build")
    folder = tmp_path_factory.mktemp("carecompass-browser")
    database = folder / "journey.db"
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for fid, name, rating, wait, lat in [
            ("000001", "Alpha Care Hospital", 5, 400, 41.88),
            ("000002", "Beta Community Hospital", 2, 20, 41.89),
            ("000003", "Gamma Review Hospital", 3, 100, None),
        ]:
            db.add(Hospital(cms_provider_id=fid, name=name, emergency_services=True,
                location=Location(address_line1="1 MAIN ST", city="CHICAGO", state="IL", zip_code="60601", latitude=lat, longitude=-87.63 if lat else None),
                quality=HospitalQuality(cms_overall_rating=rating),
                wait_time=WaitTimeEstimate(er_wait_minutes=wait),
                cms_presence=HospitalPresence(present=True, checksum="test-release", checked_on=date.today().isoformat(), release_date=date.today().isoformat())))
        db.commit()
    engine.dispose()
    api_port, web_port = free_port(), free_port()
    backend_env = {**os.environ, "DATABASE_URL": f"sqlite:///{database.as_posix()}", "CORS_ORIGINS": f"http://127.0.0.1:{web_port}", "OPENAI_API_KEY": "test-key"}
    api_log = (folder / "api.log").open("w", encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(api_port)], cwd=BACKEND, env=backend_env, stdout=api_log, stderr=subprocess.STDOUT, creationflags=flags)
    class SPAHandler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(FRONTEND/'dist'),**kwargs)
        def do_GET(self):
            if not self.path.startswith('/assets/') and self.path != '/': self.path='/'
            super().do_GET()
        def log_message(self,*args): pass
    web=ThreadingHTTPServer(('127.0.0.1',web_port),SPAHandler)
    thread=threading.Thread(target=web.serve_forever,daemon=True);thread.start()
    try:
        wait_url(f"http://127.0.0.1:{api_port}/health", api)
        with urlopen(f"http://127.0.0.1:{web_port}/",timeout=2) as response: assert response.status==200
        yield f"http://127.0.0.1:{web_port}", chrome, database, api_port
    finally:
        web.shutdown(); web.server_close(); thread.join(timeout=5)
        if api.poll() is None:
            api.terminate()
            try: api.wait(timeout=10)
            except subprocess.TimeoutExpired: api.kill(); api.wait()
        api_log.close()

def test_search_weights_profile_compare_refresh_and_failed_import(app_servers):
    base, chrome, database, api_port = app_servers
    with playwright.sync_playwright() as browser_tool:
        browser = browser_tool.chromium.launch(executable_path=str(chrome), headless=True)
        page = browser.new_page()
        page.route('http://localhost:8000/**', lambda route: route.continue_(url=route.request.url.replace('localhost:8000',f'127.0.0.1:{api_port}')))
        page.goto(base + "/search")
        page.get_by_label("City", exact=True).fill("CHICAGO")
        page.get_by_role("button", name="Search hospitals").click()
        page.get_by_text("3 hospitals found").wait_for()
        assert page.get_by_text("Alpha Care Hospital").count() >= 1
        for name in ("Alpha Care Hospital", "Beta Community Hospital"):
            card=page.locator('section[aria-live="polite"] a[href^="/hospital/"]').filter(has_text=name).last
            card.locator('xpath=..').get_by_role("button", name="Add to comparison").click()
        page.locator('section[aria-live="polite"] a[href^="/hospital/"]').filter(has_text="Alpha Care Hospital").last.click()
        page.get_by_text("Alpha Care Hospital").first.wait_for()
        page.goto(base + "/compare")
        page.get_by_role("heading", name="Compare hospitals").wait_for()
        assert page.get_by_text("Alpha Care Hospital").count() >= 1
        assert page.get_by_text("Beta Community Hospital").count() >= 1
        page.goto(base + "/rankings")
        page.get_by_role("heading", name="Top-ranked hospitals").wait_for()
        page.get_by_label("Quality Rating").fill("1")
        page.get_by_label("ED visit duration (historical)").fill("0")
        page.wait_for_timeout(600)
        assert page.locator("section[aria-live] h3").first.inner_text() == "Alpha Care Hospital"
        page.get_by_label("Quality Rating").fill("0")
        page.get_by_label("ED visit duration (historical)").fill("1")
        page.wait_for_timeout(600)
        assert page.locator("section[aria-live] h3").first.inner_text() == "Beta Community Hospital"
        page.goto(base + "/admin")
        page.get_by_role("heading", name="Data review queue").wait_for()
        page.locator("article").filter(has_text="Gamma Review Hospital").wait_for()
        page.get_by_role("button", name="Refresh now").click()
        page.get_by_text("Backups require PostgreSQL.").wait_for(timeout=30000)
        page.goto(base + "/search")
        page.get_by_text("3 hospitals found").wait_for()
        assert page.get_by_text("Gamma Review Hospital").count() >= 1
        browser.close()
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    with Session(engine) as db: assert db.query(Hospital).count() == 3
    engine.dispose()
