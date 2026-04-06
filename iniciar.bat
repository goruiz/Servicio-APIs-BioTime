@echo off
title Servicio APIs BioTime

cd /d "%~dp0"

echo.
echo ========================================
echo   Servicio APIs BioTime
echo ========================================
echo.

if not exist "venv\Scripts\uvicorn.exe" (
    echo [ERROR] No se encontro el entorno virtual.
    echo Ejecuta: python -m venv venv  y luego: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [INFO] Iniciando servidor en http://0.0.0.0:8002
echo [INFO] Presiona Ctrl+C para detener
echo.

call venv\Scripts\activate.bat
venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8002

echo.
echo [INFO] Servidor detenido.
pause
