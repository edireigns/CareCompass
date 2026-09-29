"""Interactive local launcher; starts and stops only its own child processes."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))

def prerequisites():
    missing = [m for m in ('uvicorn','fastapi','sqlalchemy','psycopg2','dotenv','openai') if importlib.util.find_spec(m) is None]
    if missing:
        raise RuntimeError('Missing backend packages: '+', '.join(missing)+'\nRun in backend: .venv\\Scripts\\python.exe -m pip install -r requirements.txt')
    if not (BACKEND / '.env').exists(): raise RuntimeError('backend/.env is missing. Restore your configuration before starting.')
    from dotenv import load_dotenv
    load_dotenv(BACKEND / '.env')
    from app.db.session import engine
    from sqlalchemy import text
    try:
        with engine.connect() as db: db.execute(text('SELECT 1'))
    except Exception:
        raise RuntimeError('Cannot connect to PostgreSQL. Start the PostgreSQL Windows service and check DATABASE_URL in backend/.env.') from None

def occupied(port):
    with socket.socket() as sock:
        return sock.connect_ex(('127.0.0.1',port)) == 0

def ready(url, backend=False):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            body=response.read().decode()
            return json.loads(body).get('app') == 'CareCompass' if backend else 'CareCompass' in body
    except Exception: return False

def launch():
    if occupied(8000) and occupied(5174) and ready('http://127.0.0.1:8000/health',True) and ready('http://127.0.0.1:5174'):
        print('CareCompass is already running. Opening it; its existing servers stay under their original launcher.')
        webbrowser.open('http://127.0.0.1:5174')
        return
    for port in (8000,5174):
        if occupied(port): raise RuntimeError(f'Port {port} is already in use. Stop the existing server in its terminal, then retry. No process was stopped.')
    node=shutil.which('node')
    if not node: raise RuntimeError('Node.js is missing. Install Node.js and then run npm.cmd install in frontend.')
    if not (ROOT/'frontend/node_modules/vite').exists(): raise RuntimeError('Frontend packages are missing. Run npm.cmd install in frontend.')
    if not (ROOT/'frontend/dist/index.html').exists(): raise RuntimeError('Frontend build is missing. Run npm.cmd run build in frontend.')
    logs=ROOT/'logs'; logs.mkdir(exist_ok=True)
    children=[]; handles=[]
    flags = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    try:
        for name,command,cwd,url,is_backend in (
            ('backend',[sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'],BACKEND,'http://127.0.0.1:8000/health',True),
            ('frontend',[node,'serve.mjs'],ROOT/'frontend','http://127.0.0.1:5174',False)):
            handle=(logs/f'{name}.log').open('w',encoding='utf-8'); handles.append(handle)
            process=subprocess.Popen(command,cwd=cwd,stdout=handle,stderr=subprocess.STDOUT,creationflags=flags)
            children.append(process)
            for _ in range(120):
                if process.poll() is not None: raise RuntimeError(f'{name.title()} stopped during startup. Read logs/{name}.log for details.')
                if ready(url,is_backend): break
                time.sleep(.5)
            else: raise RuntimeError(f'{name.title()} did not become ready. Read logs/{name}.log for details.')
        print('\nCareCompass is ready: http://127.0.0.1:5174\nKeep this window open. Press Ctrl+C to stop both servers.')
        webbrowser.open('http://127.0.0.1:5174')
        while all(p.poll() is None for p in children): time.sleep(1)
        raise RuntimeError('A server stopped. See the backend.log and frontend.log files in the logs folder.')
    except KeyboardInterrupt: print('\nStopping CareCompass...')
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
        for handle in handles: handle.close()

def restore():
    if occupied(8000) or occupied(5174): raise RuntimeError('Stop both CareCompass servers before restoring.')
    from app.services.backup_service import list_backups, restore_backup
    backups=list_backups()
    if not backups: print('No verified backups have been saved yet.'); return
    for i,b in enumerate(backups,1): print(f"{i}. {b['name']} | {b['created_at']} | {b['reason']}")
    selection=input('Archive number (Enter to cancel): ').strip()
    if not selection: return
    if not selection.isdigit() or not 1<=int(selection)<=len(backups): raise RuntimeError('Invalid backup number.')
    chosen=backups[int(selection)-1]['name']
    print(f'Replace the configured CareCompass database with {chosen}? A safety backup will be saved first.')
    confirmation=input('Type RESTORE to proceed: ').strip()
    if confirmation!='RESTORE': print('Restore cancelled.'); return
    safety=restore_backup(chosen,confirmation)
    print('Restore complete. Safety archive: '+safety['name'])

def verify():
    from app.services.backup_service import list_backups,verify_backup
    backups=list_backups()
    if not backups: print('No backups are available.'); return
    for i,b in enumerate(backups,1): print(f"{i}. {b['name']} | {b['created_at']} | {b.get('location','local')}")
    selection=input('Archive number to restore-test (Enter to cancel): ').strip()
    if not selection: return
    if not selection.isdigit() or not 1<=int(selection)<=len(backups): raise RuntimeError('Invalid backup number.')
    report=verify_backup(backups[int(selection)-1]['name'])
    print('Restore verification passed; live tables unchanged. Restored counts: '+str(report['table_counts']))

def backup_destination():
    from app.services.backup_service import configure_mirror,mirror_status
    status=mirror_status()
    print('Other-drive backup copy: '+(status['destination'] or 'not configured'))
    destination=input('Existing folder on another drive (Enter to keep, OFF to disable): ').strip()
    if not destination: return
    print(configure_mirror(None if destination.upper()=='OFF' else destination))

def main():
    prerequisites()
    while True:
        print('\nCareCompass\n1. Start both servers\n2. Back up database\n3. Restore database\n4. Verify a backup restore\n5. Configure other-drive backups\n6. Exit')
        choice=input('Choose 1-6: ').strip()
        try:
            if choice=='1': launch()
            elif choice=='2':
                from app.services.backup_service import create_backup
                print('Saved: '+create_backup('manual launcher')['name'])
            elif choice=='3': restore()
            elif choice=='4': verify()
            elif choice=='5': backup_destination()
            elif choice=='6': return
        except Exception as exc: print('\n'+str(exc))

if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: pass
    except Exception as exc: print(str(exc)); sys.exit(1)
