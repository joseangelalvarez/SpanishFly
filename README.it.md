# SpanishFly Suite (Italiano)

SpanishFly e una suite modulare di contenuti IA locale per creator che vogliono risultati professionali senza complessita tecnica.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

## Perche SpanishFly

- Workflow local-first
- Installazione one-click per utenti non tecnici
- Controlli guidati del sistema prima del setup
- Architettura modulare per pipeline completa

## Stato attuale

- Disponibile: Persona (generazione personaggi)
- Roadmap: Storyboard, Video, Voce

## Installazione one-click

- Suite completa (doppio clic): setup_spanishfly.bat
- Solo Persona (doppio clic): Persona/setup_persona.bat
- Apri app senza reinstallare: open_spanishfly.bat

Python preinstallato non e necessario.
L installer puo scaricare uv e configurare Python 3.10 automaticamente.

## Requisiti minimi

- Windows 10/11
- PowerShell 5.1+
- Internet per setup

Controlli Persona:
- OS consigliato build >= 19045
- RAM >= 16 GB
- Spazio libero >= 30 GB
- GPU NVIDIA consigliata (VRAM >= 8 GB)

Stati mostrati:
- OK
- WARN
- ERROR

Comportamento:
- ERROR blocca installazione
- WARN chiede conferma

## Installazione CLI

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_spanishfly.ps1
```

Download modelli senza prompt:

```powershell
.\setup_spanishfly.ps1 -DownloadPersonaModels -SkipModelPrompt -HfUsername "TUO_USER" -HfToken "hf_xxx"
```

## Guida rapida Hugging Face

1. Crea account: https://huggingface.co/join
2. Verifica email e accedi
3. Crea token: https://huggingface.co/settings/tokens
4. Crea token Read e copialo

Il token e salvato localmente in Persona/data/hf_credentials.json.

## Guida editor Persona

Campi principali:
- Nome personaggio (obbligatorio)
- Immagine base (opzionale)
- Prompt personaggio (obbligatorio)
- Stile immagine
- Prompt negativo (fisso + editabile)

Controlli generazione:
- Steps, CFG, Size, modalita seed
- ControlNet + posa
- Toggle NSFW

## Output

- Immagini: Persona/outputs/personas/<name>/
- Dati: Persona/data/personas/<name>.json

## Sicurezza

- Non pubblicare Persona/data/hf_credentials.json
- Evita modelli pesanti e output nella cronologia Git
