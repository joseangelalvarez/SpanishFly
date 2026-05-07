# Persona Module (SpanishFly)

Persona is the character generation module inside SpanishFly.

## Fast install (non-technical users)

1. Open the `Persona` folder.
2. Double-click `setup_persona.bat`.
3. Follow prompts in the installer window.
4. If asked, paste your Hugging Face token (`hf_...`) to download missing models.
5. Persona opens automatically when setup is complete.

You do not need to install Python manually.

## Recommended requirements

- Windows 10/11 (64-bit)
- 16 GB RAM minimum
- 30 GB free disk space minimum
- NVIDIA GPU with 8 GB VRAM recommended (CPU fallback is supported but slower)

## Important files

- `setup_persona.bat`: one-click install and launch
- `setup_persona.ps1`: full setup logic (called by the BAT file)
- `run_persona.py`: module entry point
- `config_persona.json`: local model paths and runtime defaults
- `data/hf_credentials.json`: local Hugging Face credentials (never share)

## What the installer does automatically

- Verifies minimum system requirements
- Installs `uv` if missing
- Installs Python 3.10 if missing
- Creates `Persona/venv`
- Installs PyTorch for your detected GPU profile (or CPU fallback)
- Installs module dependencies from `Persona/requirements.txt`
- Optionally downloads missing models from Hugging Face
- Launches Persona

## Troubleshooting

1. Script blocked by PowerShell:
   - Run in PowerShell: `Set-ExecutionPolicy -Scope Process Bypass`
2. Download fails from Hugging Face:
   - Verify token starts with `hf_` and has Read permission.
3. Very slow generation:
   - Without NVIDIA/CUDA, Persona runs on CPU and is significantly slower.
4. Missing model popup in UI:
   - Use the download dialog and provide valid Hugging Face credentials.

## Runtime behavior

- Persona uses local model paths from `config_persona.json` and project context.
- Long generation tasks run in background worker threads to keep UI responsive.
- Cancellation is supported and propagates to active generation work.

## Developer notes

- Layered architecture in `src/persona/`:
  - `ui/`: widgets, dialogs, signal/slot orchestration
  - `workers/`: threaded execution and cancellation signaling
  - `core/`: generation logic and persona business rules
  - `infra/`: pathing, validation, runtime checks, credentials
- Functional check:

```powershell
python functional_test_persona.py
```

- Diagnostics:

```powershell
python diagnose.py
```
