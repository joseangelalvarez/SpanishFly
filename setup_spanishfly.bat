@echo off
setlocal
cd /d "%~dp0"

echo.
echo =============================================
echo  SpanishFly - Instalador Facil
echo =============================================
echo.
echo Ejecutando instalador principal...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_spanishfly.ps1"
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
  echo Instalacion finalizada correctamente.
) else (
  echo La instalacion termino con errores. Codigo: %EXITCODE%
)
echo.
pause
exit /b %EXITCODE%
