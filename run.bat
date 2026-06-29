@echo off
REM ============================================================
REM  Lector de PDF con Voz - Ejecutar en Windows
REM  Uso: doble clic sobre este archivo .bat
REM ============================================================

title Lector de PDF con Voz
cd /d "%~dp0"

echo.
echo ============================================================
echo  Lector de PDF con Voz
echo ============================================================
echo.

REM Comprobar si Python esta instalado
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo.
    echo Descarga Python 3.10+ desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca la casilla "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b 1
)

REM Comprobar si las dependencias principales estan instaladas
python -c "import streamlit, edge_tts" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias por primera vez...
    echo Esto puede tardar varios minutos. Por favor espera.
    echo.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Hubo un problema instalando las dependencias.
        echo Ejecuta manualmente: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencias instaladas correctamente.
    echo.
)

REM ============================================================
REM  Desactivar el prompt de email del primer arranque de Streamlit
REM  y forzar el servidor en 127.0.0.1:8501
REM ============================================================
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_HEADLESS=true
set STREAMLIT_SERVER_ADDRESS=127.0.0.1
set STREAMLIT_SERVER_PORT=8501

echo [INFO] Iniciando la aplicacion...
echo [INFO] URL:  http://localhost:8501
echo [INFO] ALT:  http://127.0.0.1:8501
echo [INFO] Para detener la app, cierra esta ventana o presiona Ctrl+C.
echo.

REM Pequena pausa para asegurar que el servidor arranque
start "" /b cmd /c "timeout /t 5 /nobreak >nul && start http://127.0.0.1:8501"

python -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true

pause
