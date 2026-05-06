# SpanishFly Suite (Espanol)

SpanishFly es una suite modular de contenido con IA local, pensada para creadores que quieren resultados pro sin complejidad tecnica.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

## Por que SpanishFly

- Flujo local-first para generacion
- Instalacion en 1 clic para usuarios no tecnicos
- Chequeos guiados del sistema antes de instalar
- Arquitectura modular para pipeline completo

## Estado actual

- Disponible hoy: Persona (generador de personajes)
- En roadmap: Storyboard, Video, Voz

## Instalacion en 1 clic

- Suite completa (doble clic): setup_spanishfly.bat
- Solo Persona (doble clic): Persona/setup_persona.bat
- Abrir app sin reinstalar: open_spanishfly.bat

No necesitas Python preinstalado.
El instalador puede descargar uv y preparar Python 3.10 automaticamente.

## Requisitos minimos

- Windows 10/11
- PowerShell 5.1+
- Internet para instalacion

Chequeos Persona:
- SO recomendado build >= 19045
- RAM >= 16 GB
- Disco libre >= 30 GB
- GPU NVIDIA recomendada (VRAM >= 8 GB)

Estados del chequeo:
- OK
- WARN
- ERROR

Comportamiento:
- ERROR detiene la instalacion
- WARN pide confirmacion

## Instalacion por CLI

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_spanishfly.ps1
```

Descarga de modelos sin preguntas:

```powershell
.\setup_spanishfly.ps1 -DownloadPersonaModels -SkipModelPrompt -HfUsername "TU_USUARIO" -HfToken "hf_xxx"
```

## Guia rapida de Hugging Face

1. Crear cuenta: https://huggingface.co/join
2. Verificar email e iniciar sesion
3. Crear token: https://huggingface.co/settings/tokens
4. Crear token tipo Read y copiarlo

El token se guarda localmente en Persona/data/hf_credentials.json.

## Guia del editor Persona

Campos principales:
- Nombre del personaje (obligatorio)
- Imagen base (opcional)
- Prompt del personaje (obligatorio)
- Estilo de imagen
- Prompt negativo (fijo + editable)

Controles de generacion:
- Steps, CFG, Size, modo seed
- ControlNet + pose
- Toggle NSFW

## Salidas

- Imagenes: Persona/outputs/personas/<nombre>/
- Datos: Persona/data/personas/<nombre>.json

## Seguridad

- No publiques Persona/data/hf_credentials.json
- Evita subir modelos pesados y outputs al historial Git
