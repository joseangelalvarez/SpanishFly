---
name: spanishfly-persona-module
description: 'Diseña e implementa el modulo Persona para SpanishFly con PySide6, PyTorch/CUDA, SDXL, ControlNet e IP-Adapters usando solo modelos locales. Usar cuando se necesite preanalisis funcional/no funcional, arquitectura modular Python, matriz de compatibilidad GPU-CUDA-PyTorch, y codigo base ejecutable con cancelacion segura y UI no bloqueante.'
argument-hint: 'Describe requisitos del modulo, GPU objetivo y restricciones de modelos locales'
user-invocable: true
disable-model-invocation: false
---

# SpanishFly Persona Module

## Objetivo
Crear o evolucionar el modulo `SpanishFly/Persona` para gestion de personajes y generacion de imagen vertical con arquitectura mantenible, UX robusta y uso exclusivo de modelos locales.

Alcance por defecto: workspace (`.github/skills`).

## Cuando usar
- Cuando el usuario pida disenar el modulo Persona de `SpanishFly` de extremo a extremo.
- Cuando se requiera validar compatibilidad entre GPU, drivers, CUDA y PyTorch antes de fijar dependencias.
- Cuando se necesite una UI en PySide6 con generacion no bloqueante y cancelacion segura.
- Cuando sea obligatorio prohibir descargas remotas de modelos y trabajar con rutas locales.

## Entradas esperadas
- Nombre del proyecto y modulo (ejemplo: `SpanishFly` y `Persona`).
- Version de Python objetivo (por defecto 3.10).
- Restricciones de entorno (venv local, licencias, sin descargas remotas).
- Requisitos funcionales de UI, pipeline y persistencia JSON.
- GPU objetivo o deteccion disponible en el host (prioridad inicial: Blackwell, con fallback a Ada/Ampere).

## Flujo de trabajo
1. Preanalisis de requisitos
- Separar requisitos funcionales y no funcionales.
- Convertirlos en capacidades implementables y verificables.
- Registrar riesgos: falta de modelos locales, incompatibilidades CUDA, bloqueo de UI, cancelacion incompleta.

2. Propuesta de arquitectura
- Definir estructura de carpetas para `SpanishFly/Persona`.
- Separar modulos: `ui`, `core` (negocio), `models`, `config`, `infra` (rutas/logging/errores), `workers`.
- Definir contratos basicos entre capas (DTOs/config/resultados/eventos).

3. Estrategia de compatibilidad GPU/CUDA/PyTorch
- Detectar GPU y compute capability cuando sea posible.
- Proponer matriz compatible: PyTorch, runtime CUDA y rango de driver.
- Si no hay GPU CUDA, definir modo degradado (CPU) con advertencia clara de rendimiento.

4. Dependencias y entorno
- Crear `venv/` local Python 3.10.
- Generar `requirements.txt` del modulo con librerias necesarias para PySide6 y pipeline local (Diffusers + PyTorch como stack base; transformers/safetensors/accelerate/opencv/pillow, etc.).
- Evitar dependencias o codigo que fuerce `from_pretrained` remoto.

5. Configuracion y rutas locales
- Disenar `config_persona.json` (o equivalente) con rutas absolutas/relativas normalizadas para SDXL, ControlNet e IP-Adapters.
- Validar existencia de rutas y permisos de lectura antes de cargar modelos.
- Centralizar resolucion robusta de rutas para ejecucion desde distintos directorios.

6. UI PySide6 y experiencia de usuario
- Construir ventana principal con:
  - Nombre de personaje
  - Imagen base
  - Prompt base
  - Botones: Generar, Guardar personaje, Cancelar, Salir
- Conectar senales/slots para ejecucion asincronica y feedback de estado.
- Evitar bloqueo de UI durante generacion.

7. Pipeline de generacion
- Implementar entrada: nombre, prompt y configuracion de modelos.
- Salida: imagen vertical (por defecto 1080x1920) en `outputs/personas/<nombre>/`.
- Permitir cancelacion segura mediante bandera compartida o interrupcion controlada del worker.
- Actualizar JSON del personaje con ultima imagen generada y metadatos.

8. Robustez, licencia y extension futura
- Mensajes de error claros para CUDA no disponible, modelo faltante y carga fallida.
- Respetar LGPL de Qt: uso dinamico, sin incrustacion estatica.
- Dejar TODOs y puntos de extension para modulos `Storyboard` y `Video`.

## Decision points
- Si la GPU no es NVIDIA CUDA:
  - Mantener ejecucion CPU con aviso.
  - Reducir defaults (pasos, resolucion o precision) para evitar tiempos excesivos.
- Si la arquitectura es reciente (ej. Blackwell) y hay incertidumbre de wheel:
  - Priorizar combinacion estable documentada y anotar alternativa experimental.
- Si faltan modelos locales:
  - Fallar con mensaje accionable y no iniciar pipeline.
- Si la cancelacion es solicitada:
  - Marcar flag de parada, cerrar recursos y notificar estado final sin dejar hilos vivos.

## Criterios de calidad y cierre
- Existe preanalisis claro y trazable a cada requisito.
- Existe estructura modular concreta para `SpanishFly/Persona`.
- `requirements.txt` queda justificado con decision de compatibilidad GPU/CUDA/PyTorch.
- Codigo base compila/importa y ejecuta UI con flujo minimo funcional.
- No hay descargas remotas de modelos en runtime.
- La UI responde durante generacion y la cancelacion funciona sin procesos zombis.
- Persistencia JSON del personaje y rutas de salida funcionan.

## Entregables esperados
- Propuesta de estructura de carpetas y modulos.
- `requirements.txt` inicial con notas de compatibilidad.
- Codigo base: `main`, UI principal, gestion de config/rutas, chequeo CUDA, worker de generacion cancelable.
- Breve guia de extension a `Storyboard` y `Video`.

## Prompt sugerido para invocar este skill
`/spanishfly-persona-module Diseña e implementa el módulo Persona para SpanishFly con venv Python 3.10, PySide6, SDXL/ControlNet/IP-Adapters locales, validación CUDA y cancelación segura.`
