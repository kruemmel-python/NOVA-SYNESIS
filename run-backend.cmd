@echo off
setlocal

set PYTHONPATH=src
set HOST=127.0.0.1
set PORT=8000
set LITMODEL=

if not "%~1"=="" set HOST=%~1
if not "%~2"=="" set PORT=%~2
if not "%~3"=="" set LITMODEL=%~3

if "%LITMODEL%"=="" (
    python -m nova_synesis.cli run-api --host %HOST% --port %PORT%
) else (
    python -m nova_synesis.cli run-api --host %HOST% --port %PORT% --lit-model %LITMODEL%
)
