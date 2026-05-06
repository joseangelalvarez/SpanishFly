@echo off
setlocal
cd /d "%~dp0"

echo.
echo =============================================
echo  SpanishFly - Abrir Aplicacion
echo =============================================
echo.

if not exist "%~dp0venv\Scripts\python.exe" (
  echo No se encontro el entorno de la aplicacion.
  echo Ejecuta primero setup_spanishfly.bat para instalar.
  echo.
  pause
  exit /b 1
)

echo Abriendo launcher principal...
"%~dp0venv\Scripts\python.exe" "%~dp0launcher.py"
set "EXITCODE=%ERRORLEVEL%"

echo.
if not "%EXITCODE%"=="0" (
  echo La aplicacion se cerro con codigo: %EXITCODE%
)
echo.
pause
exit /b %EXITCODE%
