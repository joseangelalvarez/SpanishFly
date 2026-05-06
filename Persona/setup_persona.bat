@echo off
setlocal
cd /d "%~dp0"

echo.
echo =============================================
echo  Persona - Instalador Facil
echo =============================================
echo.
echo Ejecutando instalador del modulo Persona...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_persona.ps1"
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
  echo Instalacion de Persona finalizada correctamente.
) else (
  echo La instalacion de Persona termino con errores. Codigo: %EXITCODE%
)
echo.
pause
exit /b %EXITCODE%
