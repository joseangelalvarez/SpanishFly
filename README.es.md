# SpanishFly Suite — Espanol

SpanishFly es una suite modular de contenido con IA local, pensada para creadores que quieren resultados profesionales sin necesidad de conocimientos tecnicos.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

---

## Instalacion simple (recomendada)

Si no tienes experiencia tecnica, sigue solo estos pasos:

1. Descarga el ZIP del repositorio y extraelo.
2. Entra en la carpeta SpanishFly.
3. Haz doble clic en `setup_spanishfly.bat`.
4. Responde a las preguntas del instalador (si te pide token de Hugging Face, pega tu `hf_...`).
5. Espera a que termine. La app se abre sola.

No necesitas instalar Python ni tocar comandos.

---

## Que necesitas antes de empezar

Antes de instalar, asegurate de tener:

- **Windows 10 o Windows 11** (64 bits)
- **Al menos 16 GB de RAM** y **30 GB de espacio libre en disco**
- **GPU NVIDIA recomendada** con 8 GB de VRAM o mas (sin GPU se puede usar, pero es mucho mas lento)
- **Conexion a internet** para la instalacion y la descarga de modelos
- Una **cuenta gratuita en Hugging Face** para descargar los modelos de IA (ver paso 2)

---

## Paso 1 — Descarga el proyecto

1. Haz clic en el boton verde **Code** en la parte superior de esta pagina de GitHub
2. Selecciona **Download ZIP**
3. Extrae la carpeta ZIP en un lugar de tu ordenador (por ejemplo, el Escritorio o `C:\SpanishFly`)

> Tambien puedes clonar con Git si sabes usarlo: `git clone https://github.com/joseangelalvarez/SpanishFly.git`

---

## Paso 2 — Crea tu cuenta y token en Hugging Face

Los modelos de IA de SpanishFly se descargan desde Hugging Face. Necesitas una cuenta gratuita y un token de acceso.

1. Crea una cuenta en [https://huggingface.co/join](https://huggingface.co/join)
2. Verifica tu email e inicia sesion
3. Ve a [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Haz clic en **New token**, selecciona tipo **Read** y ponle un nombre (por ejemplo, `spanishfly`)
5. Copia el token — empieza por `hf_...` — lo necesitaras durante la instalacion

> El token se guarda solo en tu ordenador, en `Persona/data/hf_credentials.json`. Nunca lo compartas.

---

## Paso 3 — Ejecuta el instalador

1. Abre la carpeta donde extrajiste SpanishFly
2. Haz **doble clic** en el archivo **`setup_spanishfly.bat`**
3. Si Windows pregunta si confias en el archivo, haz clic en **"Ejecutar de todas formas"**
4. El instalador se abrira en una ventana negra (consola) y hara todo automaticamente:
   - Comprobara los requisitos de tu sistema y te avisara si algo no cumple el minimo
   - Instalara Python 3.10 automaticamente (no necesitas instalarlo tu)
   - Creara el entorno de trabajo aislado
   - Instalara todas las dependencias
   - Te preguntara si quieres descargar ahora los modelos de IA (responde S o Y e introduce tu token de Hugging Face)
5. La primera instalacion puede tardar **entre 10 y 40 minutos** segun tu conexion y si descargas los modelos

> Si Windows bloquea el script de PowerShell, ejecuta primero en PowerShell: `Set-ExecutionPolicy -Scope Process Bypass`

---

## Paso 4 — Abre la aplicacion

- Al terminar la instalacion, la aplicacion se abre automaticamente
- Para volver a abrirla en el futuro sin reinstalar, haz **doble clic** en **`open_spanishfly.bat`**

Si solo quieres instalar Persona, usa `Persona/setup_persona.bat`.

---

## Que incluye SpanishFly hoy

- **Persona** — Editor de personajes con IA: genera imagenes de personajes a partir de una descripcion, imagen de referencia y configuracion de estilo
- **Storyboard, Video, Voz** — En desarrollo

---

## Resumen de archivos importantes

| Archivo | Para que sirve |
|---|---|
| `setup_spanishfly.bat` | Instala todo (doble clic) |
| `open_spanishfly.bat` | Abre la app sin reinstalar |
| `Persona/setup_persona.bat` | Instala solo el modulo Persona |

---

## Lo que hace el instalador en detalle

El instalador comprueba tu sistema y te muestra una tabla con el resultado:

| Estado | Significado |
|---|---|
| OK | Requisito cumplido |
| WARN | Advertencia: puedes continuar pero el rendimiento puede ser menor |
| ERROR | Requisito no cumplido: la instalacion se detiene hasta que lo corrijas |

---

## Guia del editor Persona

Una vez dentro de la app, en el editor Persona:

- **Nombre del personaje** (obligatorio): identifica y guarda el personaje
- **Imagen de referencia** (opcional): foto o imagen que el modelo usara como base de estilo
- **Prompt** (obligatorio): descripcion del personaje en ingles para mejores resultados
- **Estilo de imagen**: preset visual aplicado automaticamente
- **Prompt negativo**: lo que el modelo debe evitar (ya configurado, puedes editar)
- **Steps / CFG / Tamano / Seed**: controles avanzados de generacion
- **ControlNet**: activa control de pose con imagen de referencia

Los modelos se seleccionan automaticamente segun el tipo de proyecto.

Las imagenes generadas se guardan en `Persona/outputs/personas/<nombre>/`.

---

## Seguridad

- No subas `Persona/data/hf_credentials.json` a ningun repositorio publico
- Los modelos y las imagenes generadas estan excluidos del historial de Git por defecto

---

## Solucion de problemas rapida

1. La ventana se cierra al instante:
   - Haz clic derecho en `setup_spanishfly.bat` y elige "Ejecutar como administrador".
2. PowerShell bloquea scripts:
   - Ejecuta en PowerShell: `Set-ExecutionPolicy -Scope Process Bypass`
3. Error al descargar modelos:
   - Verifica que el token empiece por `hf_` y que tenga permisos de lectura.
4. Muy lento al generar:
   - Sin GPU NVIDIA se usa CPU, que es mucho mas lenta.
