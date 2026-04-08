@echo off
setlocal

set PYTHONPATH=src
set HOST=127.0.0.1
set PORT=8000

if not "%~1"=="" set HOST=%~1
if not "%~2"=="" set PORT=%~2

python -m nova_synesis.cli run-api --host %HOST% --port %PORT%
