@echo off
REM Script de inicio rápido para Windows

REM Verificar si existe .env
if not exist .env (
    echo No se encontro archivo .env
    echo Copiando .env.example a .env...
    copy .env.example .env
    echo Archivo .env creado. Por favor configura tus credenciales de BioTime.
    exit /b 1
)

REM Activar entorno virtual de Windows (venv-win) si existe
if exist venv-win\Scripts\activate.bat (
    call venv-win\Scripts\activate.bat
) else (
    echo No se encontro entorno virtual de Windows.
    echo Crea uno con: python -m venv venv-win
    echo Luego instala dependencias: venv-win\Scripts\pip install -r requirements.txt
    exit /b 1
)

REM Verificar dependencias
pip install -q -r requirements.txt

REM Ejecutar la aplicación
python -m app.main
