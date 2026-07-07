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

REM ------------------------------------------------------------
REM 1. Verificar que Python este instalado
REM ------------------------------------------------------------
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

echo [INFO] Python detectado:
python --version
echo.

REM ------------------------------------------------------------
REM 2. Verificar dependencias una por una
REM    Si falta cualquiera, reinstalar todo el requirements.txt
REM ------------------------------------------------------------
echo [INFO] Verificando dependencias instaladas...

set MISSING_DEPS=0

for %%p in (streamlit pypdf edge_tts soundfile numpy pyttsx3) do (
    python -c "import %%p" >nul 2>&1
    if errorlevel 1 (
        echo    [FALTA] %%p
        set MISSING_DEPS=1
    ) else (
        echo    [OK]     %%p
    )
)

REM Piper y onnxruntime son opcionales (solo si se quiere usar Piper TTS)
set MISSING_PIPER=0
python -c "import piper" >nul 2>&1
if errorlevel 1 (
    echo    [AVISO] piper-tts no instalado (opcional, solo si se quiere usar Piper TTS offline)
    set MISSING_PIPER=1
)

echo.

REM ------------------------------------------------------------
REM 3. Instalar dependencias faltantes
REM ------------------------------------------------------------
if "%MISSING_DEPS%"=="1" (
    echo [INFO] Faltan dependencias. Reinstalando requirements.txt...
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
) else (
    echo [OK] Todas las dependencias estan instaladas.
    echo.
)

REM ------------------------------------------------------------
REM 4. Si falta Piper y el usuario quiere TTS offline, ofrecer instalarlo
REM ------------------------------------------------------------
if "%MISSING_PIPER%"=="1" (
    echo [INFO] Piper TTS no esta instalado. La app funciona con Edge-TTS y pyttsx3.
    echo        Si deseas usar Piper TTS offline, ejecuta manualmente:
    echo        pip install piper-tts onnxruntime
    echo.
)

REM ------------------------------------------------------------
REM 5. Configurar Streamlit (desactivar prompt email, forzar localhost)
REM ------------------------------------------------------------
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_HEADLESS=true
set STREAMLIT_SERVER_ADDRESS=127.0.0.1
set STREAMLIT_SERVER_PORT=8501

echo ============================================================
echo  Iniciando la aplicacion...
echo ============================================================
echo  URL:  http://localhost:8501
echo  ALT:  http://127.0.0.1:8501
echo  Para detener la app, cierra esta ventana o presiona Ctrl+C.
echo ============================================================
echo.

REM Abrir el navegador automaticamente a los 5 segundos
start "" /b cmd /c "timeout /t 5 /nobreak >nul && start http://127.0.0.1:8501"

REM ------------------------------------------------------------
REM 6. Arrancar Streamlit
REM ------------------------------------------------------------
python -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true

echo.
echo [INFO] La aplicacion se ha detenido.
pause
