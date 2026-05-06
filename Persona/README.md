# Persona Module (SpanishFly)

## Preanalisis de requisitos

### Funcionales
1. Gestion de entorno local con Python 3.10 y venv en `Persona/venv`.
2. Dependencias para PySide6, PyTorch/CUDA y pipeline SDXL + ControlNet + IP-Adapters.
3. Carga de modelos solo desde rutas locales configuradas en `config_persona.json`.
4. UI con nombre, prompt, imagen base y acciones de generar/guardar/cancelar/salir.
5. Generacion vertical (1080x1920 por defecto) con salida organizada en `outputs/personas/<nombre>/`.
6. Persistencia de personajes en JSON (`data/personas/<nombre>.json`) con metadatos minimos.
7. Cancelacion segura durante generacion, sin bloquear la UI.

### No funcionales
1. Arquitectura modular por capas (UI, negocio, modelos, config, infra, workers).
2. Mensajes de error claros para problemas de CUDA, rutas y carga de modelos.
3. Uso dinamico de Qt (PySide6) respetando LGPL, sin linking estatico.
4. Optimizacion base para VRAM con `float16` cuando haya CUDA.
5. Extensibilidad para modulos futuros (Storyboard y Video).

## Matriz de compatibilidad recomendada

La aplicación detecta GPU/runtime en arranque y muestra advertencias cuando hay desajustes.

- Perfil objetivo (recomendado):
  - GPU: Blackwell (CC 12.x)
  - Driver: >= 570
  - CUDA runtime: 12.8
  - PyTorch: 2.7.1+cu128
- Perfil fallback Ada/Ampere:
  - GPU: Ada (CC 8.9) o Ampere (CC 8.0/8.6)
  - CUDA runtime: 12.4 o 12.8
  - PyTorch: 2.6+ (wheel CUDA correspondiente)
- Sin CUDA disponible:
  - Modo CPU con advertencia de rendimiento

> Nota: para nuevas GPUs o cambios de wheel, ajustar `requirements.txt` y volver a ejecutar el chequeo en runtime.

## Arquitectura propuesta

```
Persona/
  venv/
  requirements.txt
  config_persona.json
  data/personas/
  models/
    sdxl/
    controlnet/
    ip_adapters/
  outputs/personas/
  src/persona/
    __init__.py
    __main__.py
    main.py
    config/
      __init__.py
      settings.py
    infra/
      __init__.py
      gpu.py
      pathing.py
      errors.py
    core/
      __init__.py
      schemas.py
      persona_store.py
      model_registry.py
      generator.py
    workers/
      __init__.py
      generation_worker.py
    ui/
      __init__.py
      main_window.py
```

## Politica de entornos

- El proyecto usa aislamiento por modulo: cada modulo tiene su propio `venv` y su propio `requirements.txt`.
- El root del repo (`SpanishFly/requirements.txt`) solo cubre el formulario principal/orquestador.
- Este modulo siempre se ejecuta con `Persona/venv`.
- La carga de modelos es exclusivamente local: no se realizan descargas de modelos en runtime.

## Trazabilidad de requisitos

- UI no bloqueante: generación en `QThread` con `GenerationWorker`.
- Cancelación segura: `threading.Event` y cancelación durante callbacks de inferencia.
- Salida vertical: defaults de `width=1080`, `height=1920` en configuración.
- Persistencia JSON: actualización de `data/personas/<nombre>.json` con última imagen y metadatos.
- Robustez local-only: validación de rutas locales antes de generar y errores accionables.

## Ejecucion

1. Crear/activar entorno virtual en `Persona/venv` con Python 3.10.
2. Instalar dependencias desde `requirements.txt`.
3. Ajustar rutas locales de modelos en `config_persona.json` y verificar que existan físicamente.
4. Ejecutar:

```powershell
python -m persona
```

## Extension futura

- Storyboard: reutilizar `core/schemas.py`, `core/persona_store.py` y `infra/pathing.py`.
- Video: reutilizar configuracion central y pipeline worker para stages de render/export.
