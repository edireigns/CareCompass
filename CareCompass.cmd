@echo off
setlocal
cd /d "%~dp0"
if defined CARECOMPASS_PYTHON goto configured
if exist "backend\.venv\Scripts\python.exe" (
  set "CARECOMPASS_PYTHON=%~dp0backend\.venv\Scripts\python.exe"
  goto configured
)
echo Backend Python environment is missing.
echo In the backend folder run: py -3 -m venv .venv
echo Then run: .venv\Scripts\python.exe -m pip install -r requirements.txt
pause
exit /b 1
:configured
"%CARECOMPASS_PYTHON%" "tools\manage.py"
if errorlevel 1 pause
