# SpanishFly Suite

SpanishFly is a modular AI content suite focused on creators who want pro results without technical complexity.

Today you can build high quality characters with Persona.
Next, the suite expands to Storyboard, Video, and Voice.

## Why SpanishFly

- Local-first generation workflow.
- One-click install experience for non-technical users.
- Guided system checks before heavy setup.
- Modular architecture designed for a full production pipeline.

## Current Product Status

- Available now: Persona (character generation module)
- In roadmap: Storyboard, Video, Voice

## What Persona Delivers

- Character generation with SDXL pipeline
- Optional ControlNet pose guidance
- Optional IP-Adapter reference support
- NSFW model toggle based on configured local model set
- Safe cancellation and responsive UI

## Technologies

Core launcher:
- Python 3.10
- PySide6
- pydantic
- PyYAML

Persona module:
- Python 3.10 (isolated module environment)
- PySide6
- PyTorch (CPU or CUDA profile)
- diffusers
- transformers
- accelerate
- ControlNet
- IP-Adapter
- huggingface-hub

Installer stack:
- PowerShell 5.1+
- uv (automatic Python bootstrap when Python is not installed)

## One-Click Install (Recommended)

### Option A: Full Suite (double click)

1. Double click setup_spanishfly.bat.
2. Follow the installer prompts.
3. Confirm execution if Windows shows a security prompt.

### Option B: Persona only (double click)

- Double click Persona/setup_persona.bat.

### Important

- Python pre-installation is not required.
- Installer can download uv and bootstrap Python 3.10 automatically.
- Persona is installed in its own isolated environment at Persona/venv.

## Minimum Requirements

General:
- Windows 10/11
- PowerShell 5.1+
- Internet connection for dependency setup

Persona validated checks:
- OS: Windows (recommended build >= 19045)
- RAM: minimum 16 GB
- Free disk: minimum 30 GB on install drive
- GPU: NVIDIA recommended (VRAM recommended >= 8 GB for SDXL)

During Persona setup, users see a clear visual status summary per requirement:
- OK
- WARN
- ERROR

Behavior:
- ERROR stops installation
- WARN asks user confirmation to continue

## CLI Install Options

Full suite:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_spanishfly.ps1
```

Install and download missing Persona models without prompts:

```powershell
.\setup_spanishfly.ps1 -DownloadPersonaModels -SkipModelPrompt -HfUsername "TU_USUARIO" -HfToken "hf_xxx"
```

Skip system checks temporarily:

```powershell
.\setup_spanishfly.ps1 -SkipSystemChecks
```

Do not launch app after setup:

```powershell
.\setup_spanishfly.ps1 -NoLaunch
```

Persona direct setup with model download:

```powershell
.\Persona\setup_persona.ps1 -DownloadModels -SkipModelPrompt -HfUsername "TU_USUARIO" -HfToken "hf_xxx"
```

## Hugging Face Quick Guide

If you want model download during setup:
1. Create account: https://huggingface.co/join
2. Verify email and sign in.
3. Open token settings: https://huggingface.co/settings/tokens
4. Create a Read token.
5. Copy token (starts with hf_) and paste it when installer asks.

Notes:
- Some model repositories require accepting terms on their model page.
- Token is stored locally at Persona/data/hf_credentials.json for reuse.

## Usage

Double click launch paths:
- setup_spanishfly.bat
- Persona/setup_persona.bat

Manual launch:

```powershell
.\venv\Scripts\python.exe .\launcher.py
```

Persona direct run after install:

```powershell
.\Persona\venv\Scripts\python.exe .\Persona\run_persona.py
```

## Persona Editor Guide

Main fields:
- Character name (required)
- Base image (optional, enables reference flow if assets exist)
- Character prompt (required)
- Image style: Photorealism, Anime, 3D, Illustration, Comic, Fantasy
- Fixed negative prompt (always applied)
- Additional negative prompt (editable)

Generation parameters:
- Sampler: DPM++ 2M SDE (fixed)
- Schedule: Exponential (fixed)
- Steps: 10 to 120
- CFG scale: 1.0 to 15.0
- Size: SDXL presets
- Seed mode: Random or Fixed
- Seed range: 0..4294967295 (fixed mode)
- Reference strength: 0.00 to 1.00
- ControlNet toggle and pose selection
- NSFW toggle using configured NSFW model

Actions:
- Generate
- Save character
- Cancel (with confirmation and clean stop)

Output:
- Images: Persona/outputs/personas/<name>/
- Character data: Persona/data/personas/<name>.json

## Product Roadmap

Storyboard:
- Turn scripts into visual scene boards
- Camera angles and continuity planning

Video:
- Animate characters from still base references
- Export production-ready clips

Voice:
- Local TTS generation
- Character voice profile export

## Repository

- Target repository: https://github.com/joseangelalvarez/SpanishFly

## Security

- Hugging Face credentials are local-only.
- Do not publish Persona/data/hf_credentials.json.
- Heavy model files and outputs should stay out of Git history.
