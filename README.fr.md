# SpanishFly Suite (Francais)

SpanishFly est une suite modulaire de creation IA locale pour obtenir des resultats pro sans complexite technique.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

## Pourquoi SpanishFly

- Workflow local-first
- Installation en 1 clic pour utilisateurs non techniques
- Verification guidee du systeme avant installation
- Architecture modulaire pour pipeline complet

## Etat actuel

- Disponible: Persona (generation de personnages)
- Roadmap: Storyboard, Video, Voix

## Installation en 1 clic

- Suite complete (double clic): setup_spanishfly.bat
- Persona seulement (double clic): Persona/setup_persona.bat
- Ouvrir sans reinstaller: open_spanishfly.bat

Python preinstalle n est pas necessaire.
Le script peut telecharger uv et installer Python 3.10 automatiquement.

## Exigences minimales

- Windows 10/11
- PowerShell 5.1+
- Internet pour l installation

Verifications Persona:
- OS recommande build >= 19045
- RAM >= 16 GB
- Espace libre >= 30 GB
- GPU NVIDIA recommande (VRAM >= 8 GB)

Statuts:
- OK
- WARN
- ERROR

Comportement:
- ERROR arrete l installation
- WARN demande confirmation

## Installation CLI

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_spanishfly.ps1
```

Telechargement des modeles sans prompts:

```powershell
.\setup_spanishfly.ps1 -DownloadPersonaModels -SkipModelPrompt -HfUsername "VOTRE_USER" -HfToken "hf_xxx"
```

## Guide rapide Hugging Face

1. Creer compte: https://huggingface.co/join
2. Verifier email et se connecter
3. Creer token: https://huggingface.co/settings/tokens
4. Creer token Read et le copier

Le token est stocke localement dans Persona/data/hf_credentials.json.

## Guide de l editeur Persona

Champs principaux:
- Nom du personnage (obligatoire)
- Image de base (optionnel)
- Prompt personnage (obligatoire)
- Style image
- Prompt negatif (fixe + editable)

Controles generation:
- Steps, CFG, Size, mode seed
- ControlNet + pose
- Toggle NSFW

## Sorties

- Images: Persona/outputs/personas/<name>/
- Donnees: Persona/data/personas/<name>.json

## Securite

- Ne pas publier Persona/data/hf_credentials.json
- Eviter de versionner les modeles lourds et outputs
