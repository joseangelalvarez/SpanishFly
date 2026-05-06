# Politica de entornos virtuales en SpanishFly

## Regla general
- Cada modulo tiene su propio `venv/` y su propio `requirements.txt`.
- El root del proyecto solo mantiene dependencias del formulario principal/orquestador.

## Estructura esperada
- `SpanishFly/requirements.txt` -> dependencias del formulario principal.
- `SpanishFly/Persona/venv` + `SpanishFly/Persona/requirements.txt`.
- `SpanishFly/Video/venv` + `SpanishFly/Video/requirements.txt` (cuando exista).

## Motivo
- Evitar conflictos entre stacks incompatibles (PyTorch/CUDA/diffusers/xformers).
- Permitir evolucion independiente por modulo.
- Reducir riesgo de romper Persona al instalar dependencias de Video.

## Ejecucion recomendada
- Formulario principal: usar el entorno root.
- Modulo Persona: usar el entorno de `Persona/venv`.
- Modulo Video: usar su propio entorno cuando se implemente.

## Distribucion a usuario final
- El lanzador principal ejecuta bootstrap automatico por modulo antes de abrirlo.
- El bootstrap detecta sistema operativo, arquitectura y perfil CUDA disponible en el host.
- Cada modulo instala dependencias en su propio `venv` sin contaminar otros modulos.
- Estado de instalacion por modulo: `venv/.module_env_state.json`.

## Interprete Python por modulo
- Cada modulo tiene su propio intérprete Python dentro de su `venv/Scripts/python.exe`.
- El `venv` copia el intérprete al crearse: cada modulo queda completamente aislado.
- El usuario final NO necesita Python instalado en el sistema.

## Bootstrap sin Python (usuario final)
- El script `setup_persona.ps1` (PowerShell) maneja el caso cero-Python:
  1. Busca `uv.exe` en PATH o en `Persona/.tools/uv.exe`.
  2. Si no existe, descarga `uv` (binario unico ~10 MB) desde GitHub Releases.
  3. Usa `uv python install 3.10` para instalar Python 3.10 de forma aislada.
  4. Crea el `venv` con ese Python → el `venv` pasa a contener su propio interprete.
  5. Instala PyTorch (segun GPU detectada) y `requirements.txt`.
- `uv` se guarda en `Persona/.tools/` para reutilizarlo sin volver a descargar.
- En ejecuciones posteriores, si el `venv` ya existe, se omiten los pasos 3-5.

## Bootstrap por modulo
- Script: `bootstrap_module_env.py`.
- Uso manual:
	- `python bootstrap_module_env.py persona`
	- `python bootstrap_module_env.py persona --force`
- El script crea/actualiza `venv`, instala PyTorch segun perfil detectado y luego `requirements.txt` del modulo.

## Descarga de modelos cuando faltan
- Persona mantiene el flujo de descarga desde Hugging Face con `usuario + token`.
- Si faltan rutas locales requeridas, la UI abre `DownloadDialog` y descarga a carpetas configuradas.
- Credenciales se guardan en `Persona/data/hf_credentials.json`.
