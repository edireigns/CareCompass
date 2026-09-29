"""Local PostgreSQL archives. Passwords never enter command arguments or logs."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
import re
from sqlalchemy import text
from app.db.session import engine
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.engine import make_url
from app.core.config import get_settings

BACKUP_DIR = Path(__file__).resolve().parents[3] / 'backups'
SETTINGS_FILE = BACKUP_DIR.parent / 'backup-settings.json'

class BackupError(RuntimeError):
    pass

def mirror_destination():
    try:
        value=json.loads(SETTINGS_FILE.read_text(encoding='utf-8')).get('destination')
    except FileNotFoundError: return None
    except (OSError,ValueError) as exc: raise BackupError('Backup destination settings are unreadable. Choose a destination again.') from exc
    return Path(value) if value else None

def configure_mirror(destination):
    if destination:
        path=Path(destination).expanduser()
        if not path.is_absolute() or not path.drive or path.drive.casefold()==BACKUP_DIR.drive.casefold():
            raise BackupError('Choose an existing folder on another drive or network share.')
        if not path.is_dir(): raise BackupError('The backup destination folder is unavailable. Connect the drive and choose an existing folder.')
        try:
            with tempfile.NamedTemporaryFile(prefix='.carecompass-check-',dir=path,delete=True) as _: pass
        except OSError as exc: raise BackupError('The backup destination is not writable.') from exc
        destination=str(path.resolve())
    SETTINGS_FILE.write_text(json.dumps({'destination':destination or None},indent=2),encoding='utf-8')
    return {'destination':destination or None,'enabled':bool(destination)}

def mirror_status():
    path=mirror_destination()
    return {'destination':str(path) if path else None,'enabled':bool(path),'available':bool(path and path.is_dir())}

def archive_files(name):
    if Path(name).name != name or not name.endswith('.dump'): raise BackupError('Choose an archive from the backup list.')
    for directory in [BACKUP_DIR,mirror_destination()]:
        if directory and (directory/name).is_file() and (directory/Path(name).with_suffix('.json')).is_file():
            return directory/name
    raise BackupError('Archive and verification manifest were not found in either configured backup location.')

def check_checksum(path):
    try:
        info=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
        checksum=hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError,ValueError) as exc: raise BackupError('Archive or verification file is missing.') from exc
    if checksum!=info.get('sha256'): raise BackupError('Archive checksum does not match. Restore cancelled.')
    return info

def pg_tool(name):
    found = shutil.which(name)
    if found: return found
    roots = Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'PostgreSQL'
    for folder in sorted(roots.glob('*/bin'), reverse=True):
        candidate = folder / (name + '.exe')
        if candidate.exists(): return str(candidate)
    raise BackupError('PostgreSQL backup tools were not found. Install the PostgreSQL command-line tools or add their bin folder to PATH.')

def connection():
    url = make_url(get_settings().database_url)
    if not url.drivername.startswith('postgresql'): raise BackupError('Backups require PostgreSQL.')
    env = os.environ.copy()
    env['PGPASSWORD'] = url.password or ''
    env['PGCONNECT_TIMEOUT'] = '10'
    args = ['--host', url.host or 'localhost', '--port', str(url.port or 5432), '--username', url.username or '', '--dbname', url.database or '']
    return args, env

def run(name, args):
    conn, env = connection()
    try:
        result = subprocess.run([pg_tool(name), *conn, *args], env=env, capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BackupError('Database backup/restore could not finish. Check PostgreSQL is running and disk space is available.') from exc
    if result.returncode:
        raise BackupError('Database backup/restore failed. Check PostgreSQL tool version, database access, and disk space. No credentials were logged.')

def validate_archive(path):
    try:
        result = subprocess.run([pg_tool('pg_restore'), '--list', str(path)], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BackupError('Could not validate the database archive.') from exc
    if result.returncode: raise BackupError('The file is not a readable PostgreSQL archive.')

def create_backup(reason='manual'):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    name = f"carecompass-{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}.dump"
    target = BACKUP_DIR / name
    temporary = target.with_suffix('.partial')
    try:
        run('pg_dump', ['--format=custom', '--no-owner', '--no-privileges', '--file', str(temporary)])
        validate_archive(temporary)
        checksum = hashlib.sha256(temporary.read_bytes()).hexdigest()
        temporary.replace(target)
        info = dict(name=name, created_at=now.isoformat(), reason=reason, sha256=checksum, bytes=target.stat().st_size)
        target.with_suffix('.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
        mirror=mirror_destination()
        if mirror:
            if not mirror.is_dir(): raise BackupError('Local backup saved, but the configured other drive is unavailable. Data change stopped.')
            second=mirror/name; partial=mirror/(name+'.partial')
            try:
                with target.open('rb') as source,partial.open('wb') as dest: shutil.copyfileobj(source,dest)
                if hashlib.sha256(partial.read_bytes()).hexdigest()!=checksum: raise BackupError('Other-drive backup failed checksum verification. Data change stopped.')
                partial.replace(second)
                second.with_suffix('.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
            except OSError as exc: raise BackupError('Local backup saved, but copying to the other drive failed. Data change stopped.') from exc
            finally: partial.unlink(missing_ok=True)
            info['mirrored_to']=str(mirror)
        return info
    finally:
        temporary.unlink(missing_ok=True)

def list_backups():
    records = []
    seen=set()
    for directory in [BACKUP_DIR,mirror_destination()]:
        if not directory or not directory.is_dir(): continue
        for path in sorted(directory.glob('*.json'), reverse=True):
            try:
                info = json.loads(path.read_text(encoding='utf-8'))
                if path.with_suffix('.dump').is_file() and info.get('name')==path.with_suffix('.dump').name and info['name'] not in seen:
                    info['location']='local' if directory==BACKUP_DIR else 'other drive'
                    report=path.with_suffix('.verification.json')
                    if report.exists(): info['verification']=json.loads(report.read_text(encoding='utf-8')).get('status')
                    records.append(info);seen.add(info['name'])
            except (ValueError, OSError,KeyError): continue
    records.sort(key=lambda item:item.get('created_at',''),reverse=True)
    return records

def verify_backup(name):
    """Restore into a disposable schema; never replace public app tables."""
    path=archive_files(name)
    report=dict(name=name,checked_at=datetime.now(timezone.utc).isoformat(),status='failed',method='disposable database schema')
    schema='carecompass_verify_'+uuid.uuid4().hex[:16]
    try:
        info=check_checksum(path)
        validate_archive(path)
        with engine.connect() as db:
            public_before=db.execute(text('SELECT count(*) FROM public.hospitals')).scalar_one()
        with tempfile.TemporaryDirectory(prefix='carecompass-verify-') as folder:
            sql=Path(folder)/'restore.sql'
            try:
                result=subprocess.run([pg_tool('pg_restore'),'--schema=public','--no-owner','--no-privileges','--file',str(sql),str(path)],capture_output=True,timeout=600)
            except (OSError,subprocess.TimeoutExpired) as exc: raise BackupError('Could not prepare the archive for a disposable restore.') from exc
            if result.returncode: raise BackupError('Could not prepare the archive for a disposable restore.')
            original=sql.read_text(encoding='utf-8')
            # pg_restore emits schema-qualified app objects. Refuse unfamiliar
            # unqualified public-schema DDL rather than risking a live write.
            commands=[line for line in original.splitlines() if line.strip() and not line.lstrip().startswith('--')]
            if any(re.search(r'\b(?:CREATE|ALTER|DROP)\s+(?:SCHEMA\s+)?public\b(?!\.)',line,re.I) for line in commands):
                raise BackupError('Archive contains unsupported public-schema DDL; disposable restore cancelled.')
            if 'public.' not in original: raise BackupError('Archive has no schema-qualified app tables; disposable restore cancelled.')
            sql.write_text(original.replace('public.',schema+'.'),encoding='utf-8')
            try:
                run('psql',['--no-psqlrc','--single-transaction','--set','ON_ERROR_STOP=1','--command',f'CREATE SCHEMA {schema};','--file',str(sql)])
                with engine.connect() as db:
                    public_after=db.execute(text('SELECT count(*) FROM public.hospitals')).scalar_one()
                    if public_after!=public_before: raise BackupError('Live hospital count changed during verification.')
                    counts={table:db.execute(text(f'SELECT count(*) FROM {schema}.{table}')).scalar_one() for table in ('hospitals','hospital_measures','hospital_directory_entries')}
                    if counts['hospitals']<1: raise BackupError('Restored archive has no hospitals.')
                    report.update(status='passed',sha256=info['sha256'],table_counts=counts,live_hospitals_unchanged=True)
            finally:
                with engine.begin() as db: db.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE'))
    except BackupError as exc:
        report['message']=str(exc)
    except Exception:
        report['message']='Disposable restore failed. The live database was not replaced; inspect PostgreSQL access and archive compatibility.'
    path.with_suffix('.verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if report['status']!='passed': raise BackupError(report['message'])
    return report

def restore_backup(name, confirmation):
    if confirmation != 'RESTORE': raise BackupError('Restore cancelled: type RESTORE to confirm replacing the database.')
    path = archive_files(name)
    check_checksum(path)
    validate_archive(path)
    safety = create_backup('before restore')
    # Rebuild the app schema so newer tables cannot block an older archive's
    # foreign-key dependencies. Cleanup and restore share ONE transaction.
    # CareCompass uses a dedicated database and the public schema exclusively.
    with tempfile.TemporaryDirectory(prefix='carecompass-restore-') as folder:
        sql = Path(folder) / 'restore.sql'
        try:
            result = subprocess.run([pg_tool('pg_restore'), '--no-owner', '--no-privileges', '--file', str(sql), str(path)], capture_output=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BackupError('Could not prepare the archive for restore; database unchanged.') from exc
        if result.returncode: raise BackupError('Could not prepare the archive for restore; database unchanged.')
        run('psql', ['--no-psqlrc', '--single-transaction', '--set', 'ON_ERROR_STOP=1', '--command', 'DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;', '--file', str(sql)])
    return safety
