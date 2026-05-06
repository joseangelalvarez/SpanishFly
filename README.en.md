# SpanishFly Suite (English)

SpanishFly is a modular AI content suite focused on creators who want professional results without technical complexity.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

## Why SpanishFly

- Local-first generation workflow
- One-click install for non-technical users
- Guided system checks before setup
- Modular architecture for a full production pipeline

## Current Status

- Available now: Persona (character generation)
- In roadmap: Storyboard, Video, Voice

## One-Click Install

- Full suite (double click): setup_spanishfly.bat
- Persona only (double click): Persona/setup_persona.bat
- Open app without reinstall: open_spanishfly.bat

No Python pre-installation is required.
The installer can download uv and bootstrap Python 3.10 automatically.

## Minimum Requirements

- Windows 10/11
- PowerShell 5.1+
- Internet connection for setup

Persona checks:
- OS recommended build >= 19045
- RAM >= 16 GB
- Free disk >= 30 GB
- NVIDIA GPU recommended (VRAM >= 8 GB)

Check statuses shown by installer:
- OK
- WARN
- ERROR

Behavior:
- ERROR stops install
- WARN asks confirmation

## CLI Install

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_spanishfly.ps1
```

Model download without prompts:

```powershell
.\setup_spanishfly.ps1 -DownloadPersonaModels -SkipModelPrompt -HfUsername "YOUR_USER" -HfToken "hf_xxx"
```

## Hugging Face Quick Guide

1. Create account: https://huggingface.co/join
2. Verify email and sign in
3. Create token: https://huggingface.co/settings/tokens
4. Create a Read token and copy it

Token is stored locally in Persona/data/hf_credentials.json.

## Persona Editor Guide

Main fields:
- Character name (required)
- Base image (optional)
- Character prompt (required)
- Image style
- Negative prompt (fixed + editable)

Main generation controls:
- Steps, CFG, Size, Seed mode
- ControlNet toggle + pose
- NSFW model toggle

## Outputs

- Images: Persona/outputs/personas/<name>/
- Character data: Persona/data/personas/<name>.json

## Security

- Do not publish Persona/data/hf_credentials.json
- Keep model files and outputs out of Git history
