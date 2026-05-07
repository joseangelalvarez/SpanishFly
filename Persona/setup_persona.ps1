#Requires -Version 5.1
<#
.SYNOPSIS
    Setup del modulo Persona de SpanishFly.
    No requiere Python pre-instalado: descarga uv si es necesario y lo usa
    para instalar Python 3.10, crear el venv local, instalar dependencias
    y lanzar la app.

.PARAMETER NoLaunch
    Si se indica, no lanza Persona al finalizar.

.PARAMETER DownloadModels
    Si se indica, intenta descargar modelos faltantes desde Hugging Face.

.PARAMETER SkipModelPrompt
    Si se indica, omite la pregunta interactiva de descarga de modelos.

.PARAMETER HfUsername
    Usuario de Hugging Face para guardar credenciales locales.

.PARAMETER HfToken
    Token de Hugging Face para descargar modelos.
#>

param(
    [switch]$NoLaunch,
    [switch]$DownloadModels,
    [switch]$SkipModelPrompt,
    [switch]$SkipSystemChecks,
    [string]$HfUsername = "",
    [string]$HfToken = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PersonaRoot = $PSScriptRoot
$VenvDir     = Join-Path $PersonaRoot "venv"
$VenvPython  = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip     = Join-Path $VenvDir "Scripts\pip.exe"
$ReqFile     = Join-Path $PersonaRoot "requirements.txt"
$EntryPoint  = Join-Path $PersonaRoot "run_persona.py"
$ToolsDir    = Join-Path $PersonaRoot ".tools"
$UvLocal     = Join-Path $ToolsDir "uv.exe"
$ConfigFile  = Join-Path $PersonaRoot "config_persona.json"
$CredsFile   = Join-Path $PersonaRoot "data\hf_credentials.json"

# Requisitos mínimos para ejecutar Persona de forma usable.
$MinWindowsBuild = 19045  # Windows 10 22H2
$MinRamGB = 16
$MinFreeDiskGB = 30
$MinGpuVramGB = 8

function Write-Step { param($msg) Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "    ERROR: $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "    INFO: $msg" -ForegroundColor Magenta }

function Test-IsWindowsHost {
    if (Get-Variable -Name IsWindows -Scope Global -ErrorAction SilentlyContinue) {
        return [bool]$Global:IsWindows
    }
    return [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
}

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

function Test-SystemRequirements {
    $checks = [System.Collections.ArrayList]::new()

    function Add-CheckResult {
        param(
            [string]$Requirement,
            [string]$Status,
            [string]$Detail
        )
        [void]$checks.Add([PSCustomObject]@{
            Requirement = $Requirement
            Status = $Status
            Detail = $Detail
        })
    }

    # SO: solo Windows y build minima recomendada
    if (-not (Test-IsWindowsHost)) {
        Add-CheckResult -Requirement "Sistema operativo" -Status "ERROR" -Detail "No compatible. Persona requiere Windows."
    } else {
        try {
            $build = [int](Get-CimInstance -ClassName Win32_OperatingSystem).BuildNumber
            if ($build -lt $MinWindowsBuild) {
                Add-CheckResult -Requirement "Sistema operativo" -Status "WARN" -Detail "Windows build $build. Recomendado >= $MinWindowsBuild."
            } else {
                Add-CheckResult -Requirement "Sistema operativo" -Status "OK" -Detail "Windows build $build."
            }
        } catch {
            Add-CheckResult -Requirement "Sistema operativo" -Status "WARN" -Detail "No se pudo leer el build de Windows."
        }
    }

    # RAM fisica total
    try {
        $ramBytes = [double](Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory
        $ramGB = [math]::Round($ramBytes / 1GB, 1)
        if ($ramGB -lt $MinRamGB) {
            Add-CheckResult -Requirement "Memoria RAM" -Status "ERROR" -Detail "$ramGB GB detectados. Minimo: $MinRamGB GB."
        } else {
            Add-CheckResult -Requirement "Memoria RAM" -Status "OK" -Detail "$ramGB GB detectados."
        }
    } catch {
        Add-CheckResult -Requirement "Memoria RAM" -Status "WARN" -Detail "No se pudo verificar RAM."
    }

    # Espacio libre en disco (unidad de Persona)
    try {
        $driveRoot = [System.IO.Path]::GetPathRoot($PersonaRoot)
        $drive = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='$($driveRoot.TrimEnd('\'))'"
        if ($drive) {
            $freeGB = [math]::Round(([double]$drive.FreeSpace) / 1GB, 1)
            if ($freeGB -lt $MinFreeDiskGB) {
                Add-CheckResult -Requirement "Espacio en disco" -Status "ERROR" -Detail "$freeGB GB libres en $driveRoot. Minimo: $MinFreeDiskGB GB."
            } else {
                Add-CheckResult -Requirement "Espacio en disco" -Status "OK" -Detail "$freeGB GB libres en $driveRoot."
            }
        } else {
            Add-CheckResult -Requirement "Espacio en disco" -Status "WARN" -Detail "No se pudo verificar espacio libre."
        }
    } catch {
        Add-CheckResult -Requirement "Espacio en disco" -Status "WARN" -Detail "No se pudo verificar espacio libre."
    }

    # GPU NVIDIA (recomendada para rendimiento)
    $nvidiaSmi = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
    if (-not $nvidiaSmi) {
        Add-CheckResult -Requirement "GPU NVIDIA" -Status "WARN" -Detail "No se detecto NVIDIA. Se usara CPU (mas lento)."
    } else {
        try {
            $gpuName = (& nvidia-smi --query-gpu=name --format=csv,noheader 2>&1 | Select-Object -First 1).Trim()
            $rawMem = (& nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>&1 | Select-Object -First 1).Trim()
            $vramGB = [math]::Round(([double]$rawMem) / 1024, 1)
            if ($vramGB -lt $MinGpuVramGB) {
                Add-CheckResult -Requirement "GPU NVIDIA" -Status "WARN" -Detail "$gpuName ($vramGB GB VRAM). Recomendado >= $MinGpuVramGB GB."
            } else {
                Add-CheckResult -Requirement "GPU NVIDIA" -Status "OK" -Detail "$gpuName ($vramGB GB VRAM)."
            }
        } catch {
            Add-CheckResult -Requirement "GPU NVIDIA" -Status "WARN" -Detail "No se pudo leer informacion de GPU."
        }
    }

    $errors = @($checks | Where-Object { $_.Status -eq "ERROR" } | ForEach-Object { "[$($_.Requirement)] $($_.Detail)" })
    $warnings = @($checks | Where-Object { $_.Status -eq "WARN" } | ForEach-Object { "[$($_.Requirement)] $($_.Detail)" })

    return [PSCustomObject]@{
        Checks = $checks
        Errors = $errors
        Warnings = $warnings
    }
}

function Show-SystemCheckSummary {
    param([Parameter(Mandatory = $true)]$SystemCheck)

    Write-Host "    Resumen de requisitos:" -ForegroundColor Cyan
    Write-Host "    -------------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "    Estado       Requisito            Detalle" -ForegroundColor Gray
    Write-Host "    -------------------------------------------------------------------------------" -ForegroundColor DarkGray

    foreach ($check in $SystemCheck.Checks) {
        $status = [string]$check.Status
        $statusPadded = $status.PadRight(11)
        $reqPadded = ([string]$check.Requirement).PadRight(20)
        $detail = [string]$check.Detail

        $color = "White"
        if ($status -eq "OK") {
            $color = "Green"
        } elseif ($status -eq "WARN") {
            $color = "Yellow"
        } elseif ($status -eq "ERROR") {
            $color = "Red"
        }

        Write-Host "    $statusPadded $reqPadded $detail" -ForegroundColor $color
    }

    Write-Host "    -------------------------------------------------------------------------------" -ForegroundColor DarkGray
}

function Save-HfCredentials {
    param(
        [string]$Username,
        [string]$Token
    )

    if ([string]::IsNullOrWhiteSpace($Token)) {
        return
    }

    $payload = @{
        username = $Username
        token = $Token
    } | ConvertTo-Json -Depth 3

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $CredsFile) | Out-Null
    Set-Content -Path $CredsFile -Value $payload -Encoding UTF8
    Write-Ok "Credenciales de Hugging Face guardadas en data/hf_credentials.json"
}

function Get-DownloadTasksFromConfig {
    if (-not (Test-Path $ConfigFile)) {
        Write-Info "No existe config_persona.json; se omite descarga de modelos."
        return @()
    }

    $cfg = Get-Content $ConfigFile -Raw | ConvertFrom-Json
    $models = $cfg.models
    $tasks = [System.Collections.ArrayList]::new()

    function Add-Task {
        param([string]$Label, [string]$Repo, [string]$RelativePath)

        if ([string]::IsNullOrWhiteSpace($Repo) -or [string]::IsNullOrWhiteSpace($RelativePath)) {
            return
        }
        $localPath = Join-Path $PersonaRoot $RelativePath
        if (Test-Path $localPath) {
            return
        }
        [void]$tasks.Add([PSCustomObject]@{
            label = $Label
            repo = $Repo
            local = $localPath
        })
    }

    Add-Task -Label "SDXL Base" -Repo $models.sdxl_hf_repo -RelativePath $models.sdxl_base_path
    Add-Task -Label "SDXL NSFW" -Repo $models.sdxl_nsfw_hf_repo -RelativePath $models.sdxl_nsfw_path

    if ($models.controlnet_paths -and $models.controlnet_hf_repos) {
        for ($i = 0; $i -lt $models.controlnet_paths.Count; $i++) {
            $repo = if ($i -lt $models.controlnet_hf_repos.Count) { $models.controlnet_hf_repos[$i] } else { "" }
            Add-Task -Label "ControlNet $($i + 1)" -Repo $repo -RelativePath $models.controlnet_paths[$i]
        }
    }

    if ($models.ip_adapter_paths -and $models.ip_adapter_hf_repos) {
        foreach ($prop in $models.ip_adapter_paths.PSObject.Properties) {
            $key = [string]$prop.Name
            $pathValue = [string]$prop.Value
            $repo = ""
            if ($models.ip_adapter_hf_repos.PSObject.Properties.Name -contains $key) {
                $repo = [string]$models.ip_adapter_hf_repos.$key
            }
            Add-Task -Label "IP-Adapter ($key)" -Repo $repo -RelativePath $pathValue
        }
    }

    return ,$tasks
}

function Download-MissingModels {
    param(
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $true)][array]$Tasks
    )

    if ($Tasks.Count -eq 0) {
        Write-Ok "No hay modelos faltantes para descargar."
        return
    }

    Write-Step "Descargando modelos faltantes desde Hugging Face..."
    Write-Host "    Modelos pendientes: $($Tasks.Count)" -ForegroundColor Yellow

    $tasksJson = $Tasks | ConvertTo-Json -Depth 5 -Compress
    $env:SPANISHFLY_HF_TOKEN = $Token
    $env:SPANISHFLY_DOWNLOAD_TASKS_JSON = $tasksJson

    $pyScript = @'
import json
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except Exception as exc:
    print(f"ERROR: huggingface_hub no disponible: {exc}")
    raise SystemExit(1)

token = os.environ.get("SPANISHFLY_HF_TOKEN", "").strip()
raw = os.environ.get("SPANISHFLY_DOWNLOAD_TASKS_JSON", "")
if not token:
    print("ERROR: token de Hugging Face vacio")
    raise SystemExit(1)
if not raw:
    print("ERROR: no hay tareas de descarga")
    raise SystemExit(1)

tasks = json.loads(raw)
ignore_patterns = [
    "*.onnx", "*.onnx_data",
    "openvino_*", "onnx/*", "onnx_fp16/*",
    "*.msgpack", "*.h5",
    "flax_model*", "tf_model*", "rust_model*", "*.pb",
    "sd_xl_base_1.0_0.9vae.safetensors",
    "*.png", "*.jpg", "*.jpeg",
]

for idx, task in enumerate(tasks, start=1):
    label = task.get("label", "modelo")
    repo = task.get("repo", "").strip()
    local = task.get("local", "").strip()
    if not repo or not local:
        print(f"[{idx}/{len(tasks)}] Saltando tarea invalida: {task}")
        continue

    dst = Path(local)
    dst.mkdir(parents=True, exist_ok=True)
    print(f"[{idx}/{len(tasks)}] Descargando {label}: {repo}")
    try:
        snapshot_download(
            repo_id=repo,
            local_dir=str(dst),
            token=token,
            ignore_patterns=ignore_patterns,
        )
        print(f"[{idx}/{len(tasks)}] OK {label}")
    except Exception as exc:
        print(f"[{idx}/{len(tasks)}] ERROR {label}: {exc}")
        raise

print("DESCARGA_COMPLETA")
'@

    try {
        & $VenvPython -m pip install --quiet --upgrade huggingface-hub
        & $VenvPython -c $pyScript
        if ($LASTEXITCODE -ne 0) {
            throw "La descarga de modelos finalizo con codigo $LASTEXITCODE"
        }
        Write-Ok "Modelos descargados correctamente."
    } catch {
        Write-Fail "No se pudieron descargar modelos: $_"
        throw
    } finally {
        Remove-Item Env:SPANISHFLY_HF_TOKEN -ErrorAction SilentlyContinue
        Remove-Item Env:SPANISHFLY_DOWNLOAD_TASKS_JSON -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# Pre-chequeo de requisitos del sistema
# ---------------------------------------------------------------------------
if (-not $SkipSystemChecks) {
    Write-Step "Validando requisitos minimos del sistema para Persona..."
    $sysCheck = Test-SystemRequirements
    Show-SystemCheckSummary -SystemCheck $sysCheck

    if ($sysCheck.Warnings.Count -gt 0) {
        Write-Host "    Advertencias detectadas:" -ForegroundColor Yellow
        foreach ($w in $sysCheck.Warnings) {
            Write-Host "      - $w" -ForegroundColor Yellow
        }
    }

    if ($sysCheck.Errors.Count -gt 0) {
        Write-Fail "El equipo no cumple los requisitos minimos para Persona:"
        foreach ($e in $sysCheck.Errors) {
            Write-Host "      - $e" -ForegroundColor Red
        }
        Write-Host "\nRecomendacion: corrige los puntos anteriores y vuelve a ejecutar el instalador." -ForegroundColor Yellow
        Write-Host "Si necesitas continuar bajo tu responsabilidad, ejecuta con -SkipSystemChecks." -ForegroundColor Yellow
        exit 1
    }

    if ($sysCheck.Warnings.Count -gt 0) {
        $continueAnyway = Read-YesNo -Question "Hay advertencias de rendimiento/compatibilidad. ¿Continuar instalacion?" -DefaultYes $true
        if (-not $continueAnyway) {
            Write-Info "Instalacion cancelada por el usuario tras revisar advertencias."
            exit 0
        }
    }

    Write-Ok "Requisitos minimos verificados."
} else {
    Write-Info "Se omitio validacion de requisitos por parametro -SkipSystemChecks."
}

# ---------------------------------------------------------------------------
# 0. Obtener uv (gestor de Python/venv sin dependencias externas)
# ---------------------------------------------------------------------------
Write-Step "Verificando uv (gestor de entornos)..."

$uvCmd = $null

# Comprobar uv en PATH
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    $uvCmd = "uv"
    Write-Ok "uv encontrado en PATH: $(uv --version 2>&1)"
}

# Comprobar uv local en .tools/
if (-not $uvCmd -and (Test-Path $UvLocal)) {
    $uvCmd = $UvLocal
    Write-Ok "uv encontrado en .tools\: $($($UvLocal | & $UvLocal --version 2>&1))"
}

# Descargar uv si no existe
if (-not $uvCmd) {
    Write-Host "    uv no encontrado. Descargando uv (binario unico, ~10 MB)..." -ForegroundColor Yellow
    $uvZip = Join-Path $env:TEMP "uv_setup.zip"
    $uvUrl = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
    try {
        New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $uvUrl -OutFile $uvZip -UseBasicParsing
        Expand-Archive -Path $uvZip -DestinationPath $ToolsDir -Force
        Remove-Item $uvZip -ErrorAction SilentlyContinue
        # uv.exe puede quedar en subdirectorio dentro del zip
        $uvFound = Get-ChildItem -Path $ToolsDir -Recurse -Filter "uv.exe" | Select-Object -First 1
        if ($uvFound -and $uvFound.FullName -ne $UvLocal) {
            Move-Item -Path $uvFound.FullName -Destination $UvLocal -Force
        }
        $uvCmd = $UvLocal
        Write-Ok "uv descargado: $(&$uvCmd --version 2>&1)"
    } catch {
        Write-Fail "No se pudo descargar uv: $_"
        Write-Host "  Instala uv manualmente desde https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
        Read-Host "`nPresiona Enter para salir"
        exit 1
    }
}

# ---------------------------------------------------------------------------
# 1. Buscar o instalar Python 3.10 via uv
# ---------------------------------------------------------------------------
Write-Step "Buscando Python 3.10..."

$python310 = $null

# Intentar py launcher (Windows)
try {
    $ver = & py -3.10 --version 2>&1
    if ($ver -match "Python 3\.10") {
        $python310 = (& py -3.10 -c "import sys; print(sys.executable)" 2>&1).Trim()
        Write-Ok "Encontrado via py launcher: $ver -> $python310"
    }
} catch {}

# Intentar python3.10 directo
if (-not $python310) {
    try {
        $ver = & python3.10 --version 2>&1
        if ($ver -match "Python 3\.10") {
            $python310 = (& python3.10 -c "import sys; print(sys.executable)" 2>&1).Trim()
            Write-Ok "Encontrado via python3.10: $ver"
        }
    } catch {}
}

# Intentar python y verificar version
if (-not $python310) {
    try {
        $ver = & python --version 2>&1
        if ($ver -match "Python 3\.10") {
            $python310 = (& python -c "import sys; print(sys.executable)" 2>&1).Trim()
            Write-Ok "Encontrado via python: $ver"
        }
    } catch {}
}

# Instalar Python 3.10 via uv si no se encontro en el sistema
if (-not $python310) {
    Write-Host "    Python 3.10 no encontrado en el sistema. Instalando via uv..." -ForegroundColor Yellow
    try {
        & $uvCmd python install 3.10
        $python310 = (& $uvCmd python find 3.10 2>&1).Trim()
        if (-not $python310 -or -not (Test-Path $python310)) {
            throw "uv python find 3.10 no devolvio una ruta valida."
        }
        $ver = & $python310 --version 2>&1
        Write-Ok "Python 3.10 instalado via uv: $ver -> $python310"
    } catch {
        Write-Fail "No se pudo instalar Python 3.10: $_"
        Read-Host "`nPresiona Enter para salir"
        exit 1
    }
}

# ---------------------------------------------------------------------------
# 2. Crear entorno virtual si no existe
# ---------------------------------------------------------------------------
Write-Step "Verificando entorno virtual en: $VenvDir"

if (-not (Test-Path $VenvPython)) {
    Write-Host "    Creando venv con Python 3.10 ($python310)..." -ForegroundColor Yellow
    try {
        & $python310 -m venv $VenvDir
        Write-Ok "Entorno virtual creado."
    } catch {
        Write-Fail "No se pudo crear el entorno virtual: $_"
        exit 1
    }
} else {
    Write-Ok "Entorno virtual ya existe, omitiendo creacion."
}

# ---------------------------------------------------------------------------
# 3. Actualizar pip
# ---------------------------------------------------------------------------
Write-Step "Actualizando pip..."
try {
    & $VenvPython -m pip install --upgrade pip --quiet
    Write-Ok "pip actualizado."
} catch {
    Write-Fail "No se pudo actualizar pip: $_"
    exit 1
}

# ---------------------------------------------------------------------------
# 4. Detectar GPU y elegir wheel de PyTorch
# ---------------------------------------------------------------------------
Write-Step "Detectando GPU y arquitectura CUDA..."

# Matriz de compatibilidad:
#   CC 12.x  -> Blackwell (RTX 50xx)      -> cu128
#   CC 8.9   -> Ada Lovelace (RTX 40xx)   -> cu128
#   CC 8.6/8.0 -> Ampere (RTX 30xx / Ax) -> cu124
#   CC 7.5   -> Turing (RTX 20xx/GTX 16) -> cu118
#   CC 7.0   -> Volta (V100)              -> cu118
#   Sin NVIDIA o CC < 7.0                 -> cpu

$torchIndex  = "https://download.pytorch.org/whl/cpu"
$torchSuffix = "cpu"
$torchVer    = "2.11.0"
$tvVer       = "0.26.0"
$taVer       = "2.11.0"

$nvidiaSmi = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    try {
        $rawCC = & nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>&1 |
                 Select-Object -First 1
        $rawCC = $rawCC.Trim()
        Write-Host "    Compute Capability detectado: $rawCC" -ForegroundColor Magenta

        $ccMajor = [int]($rawCC.Split(".")[0])
        $ccMinor = [int]($rawCC.Split(".")[1])
        $cc = $ccMajor * 10 + $ccMinor   # 120, 89, 86, 80, 75, 70 ...

        if ($cc -ge 120) {
            # Blackwell y futuras generaciones
            $torchSuffix = "cu128"; $torchIndex = "https://download.pytorch.org/whl/cu128"
        } elseif ($cc -ge 89) {
            # Ada Lovelace (RTX 40xx)
            $torchSuffix = "cu128"; $torchIndex = "https://download.pytorch.org/whl/cu128"
        } elseif ($cc -ge 80) {
            # Ampere (RTX 30xx, A100, A10...)
            $torchSuffix = "cu124"; $torchIndex = "https://download.pytorch.org/whl/cu124"
        } elseif ($cc -ge 70) {
            # Turing (RTX 20xx, GTX 16xx) y Volta
            $torchSuffix = "cu118"; $torchIndex = "https://download.pytorch.org/whl/cu118"
        } else {
            Write-Host "    GPU NVIDIA detectada pero CC < 7.0: usando CPU." -ForegroundColor Yellow
        }
        Write-Ok "Wheel seleccionado: torch $torchVer+$torchSuffix"
    } catch {
        Write-Host "    No se pudo leer CC, usando CPU como fallback." -ForegroundColor Yellow
    }
} else {
    Write-Host "    nvidia-smi no encontrado. Instalando PyTorch CPU." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# 5. Instalar PyTorch segun arquitectura
# ---------------------------------------------------------------------------
Write-Step "Instalando PyTorch ($torchSuffix)..."
Write-Host "    (Puede tardar varios minutos segun velocidad de descarga.)" -ForegroundColor Yellow

if ($torchSuffix -eq "cpu") {
    $torchPackages = @(
        "torch==$torchVer",
        "torchvision==$tvVer",
        "torchaudio==$taVer"
    )
} else {
    $torchPackages = @(
        "torch==${torchVer}+${torchSuffix}",
        "torchvision==${tvVer}+${torchSuffix}",
        "torchaudio==${taVer}+${torchSuffix}"
    )
}

try {
    & $VenvPip install --extra-index-url $torchIndex @torchPackages
    Write-Ok "PyTorch instalado."
} catch {
    Write-Fail "Fallo al instalar PyTorch: $_"
    exit 1
}

# ---------------------------------------------------------------------------
# 6. Instalar resto de dependencias
# ---------------------------------------------------------------------------
Write-Step "Instalando dependencias base desde requirements.txt..."

if (-not (Test-Path $ReqFile)) {
    Write-Fail "No se encontro requirements.txt en: $ReqFile"
    exit 1
}

try {
    & $VenvPip install -r $ReqFile
    if ($LASTEXITCODE -ne 0) {
        throw "pip devolvio codigo de salida $LASTEXITCODE al instalar requirements.txt"
    }
    Write-Ok "Dependencias instaladas."
} catch {
    Write-Fail "Fallo al instalar dependencias: $_"
    Write-Host "    Revisa requirements.txt y la conexion a internet."
    exit 1
}

# ---------------------------------------------------------------------------
# 7. Verificar CUDA disponible
# ---------------------------------------------------------------------------
Write-Step "Verificando disponibilidad de CUDA en PyTorch..."
$cudaCheck = & $VenvPython -c "import torch; print('CUDA:' + str(torch.cuda.is_available()) + ' | GPU:' + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'))" 2>&1
Write-Host "    $cudaCheck" -ForegroundColor Magenta

# ---------------------------------------------------------------------------
# 8. Descarga opcional de modelos (Hugging Face)
# ---------------------------------------------------------------------------
if (-not $DownloadModels -and -not $SkipModelPrompt) {
    $DownloadModels = Read-YesNo -Question "¿Quieres descargar ahora los modelos faltantes de Persona desde Hugging Face?" -DefaultYes $true
}

if ($DownloadModels) {
    $tasks = Get-DownloadTasksFromConfig

    if ($tasks.Count -eq 0) {
        Write-Ok "No se detectaron modelos faltantes; no hay descargas pendientes."
    } else {
        if ([string]::IsNullOrWhiteSpace($HfUsername)) {
            $HfUsername = (Read-Host "Usuario de Hugging Face (opcional para guardar)").Trim()
        }
        if ([string]::IsNullOrWhiteSpace($HfToken)) {
            $HfToken = (Read-Host "Token de Hugging Face (hf_...)").Trim()
        }
        if ([string]::IsNullOrWhiteSpace($HfToken)) {
            Write-Fail "No se puede descargar sin token de Hugging Face."
            exit 1
        }

        Save-HfCredentials -Username $HfUsername -Token $HfToken
        Download-MissingModels -Token $HfToken -Tasks $tasks
    }
}

# ---------------------------------------------------------------------------
# 9. Lanzar aplicacion
# ---------------------------------------------------------------------------
if ($NoLaunch) {
    Write-Step "Instalacion de Persona completada."
    Write-Ok "NoLaunch activo: no se abre la aplicacion automaticamente."
    exit 0
}

Write-Step "Lanzando SpanishFly Persona..."

$SrcDir = Join-Path $PersonaRoot "src"
$env:PYTHONPATH = $SrcDir

try {
    & $VenvPython $EntryPoint
} catch {
    Write-Fail "Error al lanzar la aplicacion: $_"
    exit 1
}
