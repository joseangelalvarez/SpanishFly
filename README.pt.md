# SpanishFly Suite (Portugues)

SpanishFly e uma suite modular de conteudo com IA local para criadores que querem resultado profissional sem complexidade tecnica.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

## Por que SpanishFly

- Fluxo local-first
- Instalacao em 1 clique para usuarios nao tecnicos
- Checagens guiadas do sistema antes do setup
- Arquitetura modular para pipeline completo

## Status atual

- Disponivel: Persona (geracao de personagens)
- Roadmap: Storyboard, Video, Voz

## Instalacao em 1 clique

- Suite completa (duplo clique): setup_spanishfly.bat
- Apenas Persona (duplo clique): Persona/setup_persona.bat
- Abrir app sem reinstalar: open_spanishfly.bat

Nao precisa ter Python preinstalado.
O instalador pode baixar uv e configurar Python 3.10 automaticamente.

## Requisitos minimos

- Windows 10/11
- PowerShell 5.1+
- Internet para setup

Checagens Persona:
- SO recomendado build >= 19045
- RAM >= 16 GB
- Disco livre >= 30 GB
- GPU NVIDIA recomendada (VRAM >= 8 GB)

Status exibidos:
- OK
- WARN
- ERROR

Comportamento:
- ERROR interrompe instalacao
- WARN pede confirmacao

## Instalacao via CLI

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_spanishfly.ps1
```

Download de modelos sem perguntas:

```powershell
.\setup_spanishfly.ps1 -DownloadPersonaModels -SkipModelPrompt -HfUsername "SEU_USER" -HfToken "hf_xxx"
```

## Guia rapido Hugging Face

1. Criar conta: https://huggingface.co/join
2. Verificar email e entrar
3. Criar token: https://huggingface.co/settings/tokens
4. Criar token Read e copiar

Token fica salvo localmente em Persona/data/hf_credentials.json.

## Guia do editor Persona

Campos principais:
- Nome do personagem (obrigatorio)
- Imagem base (opcional)
- Prompt do personagem (obrigatorio)
- Estilo de imagem
- Prompt negativo (fixo + editavel)

Controles de geracao:
- Steps, CFG, Size, modo seed
- ControlNet + pose
- Toggle NSFW

## Saidas

- Imagens: Persona/outputs/personas/<name>/
- Dados: Persona/data/personas/<name>.json

## Seguranca

- Nao publique Persona/data/hf_credentials.json
- Evite modelos pesados e outputs no historico Git
