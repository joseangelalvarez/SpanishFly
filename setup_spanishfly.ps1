#Requires -Version 5.1
<#
.SYNOPSIS
    Instalador facil de SpanishFly (suite completa actual).

.DESCRIPTION
    - Prepara entorno root para el launcher principal.
    - Ejecuta instalacion de Persona en su propio venv aislado.
    - Puede descargar modelos de Persona durante la instalacion.

.PARAMETER SkipPersona
    Omite la instalacion del modulo Persona.

.PARAMETER DownloadPersonaModels
    Fuerza descarga de modelos faltantes de Persona.

.PARAMETER SkipModelPrompt
    Omite la pregunta interactiva de descarga de modelos.

.PARAMETER SkipSystemChecks
    Omite la validacion minima de requisitos de sistema en Persona.

.PARAMETER NoLaunch
    No abre el launcher al finalizar.

.PARAMETER HfUsername
    Usuario de Hugging Face para guardar credenciales en Persona.

.PARAMETER HfToken
    Token de Hugging Face para descarga de modelos.
#>

param(
    [switch]$SkipPersona,
    [switch]$DownloadPersonaModels,
    [switch]$SkipModelPrompt,
    [switch]$SkipSystemChecks,
    [switch]$NoLaunch,
    [string]$HfUsername = "",
    [string]$HfToken = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
$RootReq = Join-Path $RootDir "requirements.txt"
$RootVenvDir = Join-Path $RootDir "venv"
$RootVenvPython = Join-Path $RootVenvDir "Scripts\python.exe"
$ToolsDir = Join-Path $RootDir ".tools"
$UvLocal = Join-Path $ToolsDir "uv.exe"
$PersonaSetup = Join-Path $RootDir "Persona\setup_persona.ps1"

function Write-Step { param($msg) Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "    ERROR: $msg" -ForegroundColor Red }

function Read-YesNo {
    param(
        [Parameter(Mandatory = $true)][string]$Question,
        [bool]$DefaultYes = $true
    )

    $suffix = if ($DefaultYes) { "[Y/n]" } else { "[y/N]" }
    $raw = (Read-Host "$Question $suffix").Trim().ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return $DefaultYes
    }
    return $raw -in @("y", "yes", "s", "si")
}

function Resolve-UvCommand {
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        Write-Ok "uv encontrado en PATH: $(uv --version 2>&1)"
        return "uv"
    }

    if (Test-Path $UvLocal) {
        Write-Ok "uv encontrado en .tools: $(&$UvLocal --version 2>&1)"
        return $UvLocal
    }

    Write-Host "    uv no encontrado. Descargando uv..." -ForegroundColor Yellow
    $uvZip = Join-Path $env:TEMP "uv_setup_root.zip"
    $uvUrl = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
    New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $uvUrl -OutFile $uvZip -UseBasicParsing
    Expand-Archive -Path $uvZip -DestinationPath $ToolsDir -Force
    Remove-Item $uvZip -ErrorAction SilentlyContinue

    $uvFound = Get-ChildItem -Path $ToolsDir -Recurse -Filter "uv.exe" | Select-Object -First 1
    if (-not $uvFound) {
        throw "No se pudo encontrar uv.exe despues de la descarga."
    }
    if ($uvFound.FullName -ne $UvLocal) {
        Move-Item -Path $uvFound.FullName -Destination $UvLocal -Force
    }

    Write-Ok "uv descargado: $(&$UvLocal --version 2>&1)"
    return $UvLocal
}

function Resolve-Python310 {
    param([Parameter(Mandatory = $true)][string]$UvCmd)

    $python310 = $null

    try {
        $ver = & py -3.10 --version 2>&1
        if ($ver -match "Python 3\.10") {
            $python310 = (& py -3.10 -c "import sys; print(sys.executable)" 2>&1).Trim()
            Write-Ok "Python 3.10 via py launcher: $python310"
        }
    } catch {}

    if (-not $python310) {
        try {
            $ver = & python3.10 --version 2>&1
            if ($ver -match "Python 3\.10") {
                $python310 = (& python3.10 -c "import sys; print(sys.executable)" 2>&1).Trim()
                Write-Ok "Python 3.10 via python3.10: $python310"
            }
        } catch {}
    }

    if (-not $python310) {
        try {
            $ver = & python --version 2>&1
            if ($ver -match "Python 3\.10") {
                $python310 = (& python -c "import sys; print(sys.executable)" 2>&1).Trim()
                Write-Ok "Python 3.10 via python: $python310"
            }
        } catch {}
    }

    if (-not $python310) {
        Write-Host "    Python 3.10 no encontrado. Instalando via uv..." -ForegroundColor Yellow
        & $UvCmd python install 3.10
        $python310 = (& $UvCmd python find 3.10 2>&1).Trim()
        if (-not $python310 -or -not (Test-Path $python310)) {
            throw "uv python find 3.10 no devolvio una ruta valida."
        }
        Write-Ok "Python 3.10 instalado: $python310"
    }

    return $python310
}

try {
    Write-Step "Preparando herramientas base (uv + Python 3.10)..."
    $uvCmd = Resolve-UvCommand
    $python310 = Resolve-Python310 -UvCmd $uvCmd

    Write-Step "Preparando entorno root para launcher..."
    if (-not (Test-Path $RootVenvPython)) {
        & $python310 -m venv $RootVenvDir
        Write-Ok "Entorno root creado en venv/."
    } else {
        Write-Ok "Entorno root ya existe."
    }

    if (-not (Test-Path $RootReq)) {
        throw "No existe requirements.txt en root."
    }

    & $RootVenvPython -m pip install --upgrade pip --quiet
    & $RootVenvPython -m pip install -r $RootReq
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo instalando dependencias root (requirements.txt)."
    }
    Write-Ok "Dependencias root instaladas."

    if (-not $SkipPersona) {
        Write-Step "Instalando modulo Persona (venv aislado)..."
        if (-not (Test-Path $PersonaSetup)) {
            throw "No existe Persona/setup_persona.ps1"
        }

        $personaArgs = @("-NoLaunch")
        if ($DownloadPersonaModels) {
            $personaArgs += "-DownloadModels"
        }
        if ($SkipModelPrompt) {
            $personaArgs += "-SkipModelPrompt"
        }
        if ($SkipSystemChecks) {
            $personaArgs += "-SkipSystemChecks"
        }
        if (-not [string]::IsNullOrWhiteSpace($HfUsername)) {
            $personaArgs += "-HfUsername"
            $personaArgs += $HfUsername
        }
        if (-not [string]::IsNullOrWhiteSpace($HfToken)) {
            $personaArgs += "-HfToken"
            $personaArgs += $HfToken
        }

        & $PersonaSetup @personaArgs
        if ($LASTEXITCODE -ne 0) {
            throw "La instalacion de Persona fallo con codigo $LASTEXITCODE"
        }
        Write-Ok "Modulo Persona listo."
    } else {
        Write-Ok "Se omitio instalacion de Persona por parametro SkipPersona."
    }

    if ($NoLaunch) {
        Write-Step "Instalacion completada."
        Write-Ok "NoLaunch activo: no se abrira el launcher."
        exit 0
    }

    $launchNow = Read-YesNo -Question "Instalacion completa. ¿Abrir ahora SpanishFly Launcher?" -DefaultYes $true
    if ($launchNow) {
        Write-Step "Abriendo launcher principal..."
        & $RootVenvPython (Join-Path $RootDir "launcher.py")
    } else {
        Write-Step "Instalacion completada."
        Write-Ok "Puedes abrir el launcher luego con: .\\venv\\Scripts\\python.exe .\\launcher.py"
    }

} catch {
    Write-Fail "Instalacion detenida: $_"
    exit 1
}
