# SpanishFly Suite — English

SpanishFly is a modular local AI content suite for creators who want professional results without technical complexity.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

---

## What you need before starting

Before installing, make sure you have:

- **Windows 10 or Windows 11** (64-bit)
- **At least 16 GB of RAM** and **30 GB of free disk space**
- **NVIDIA GPU recommended** with 8 GB VRAM or more (CPU works too, but is much slower)
- **Internet connection** for installation and model download
- A **free Hugging Face account** to download the AI models (see step 2)

---

## Step 1 — Download the project

1. Click the green **Code** button at the top of this GitHub page
2. Select **Download ZIP**
3. Extract the ZIP folder somewhere on your computer (e.g., Desktop or `C:\SpanishFly`)

> You can also clone with Git if you know how: `git clone https://github.com/joseangelalvarez/SpanishFly.git`

---

## Step 2 — Create your Hugging Face account and token

SpanishFly downloads its AI models from Hugging Face. You need a free account and an access token.

1. Create an account at [https://huggingface.co/join](https://huggingface.co/join)
2. Verify your email and sign in
3. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Click **New token**, select type **Read**, and give it a name (e.g., `spanishfly`)
5. Copy the token — it starts with `hf_...` — you will need it during installation

> The token is stored only on your computer, in `Persona/data/hf_credentials.json`. Never share it.

---

## Step 3 — Run the installer

1. Open the folder where you extracted SpanishFly
2. **Double-click** the file **`setup_spanishfly.bat`**
3. If Windows asks whether you trust the file, click **"Run anyway"**
4. The installer will open in a black window (console) and do everything automatically:
   - Check your system requirements and warn you if something is below the minimum
   - Install Python 3.10 automatically (you do not need to install it yourself)
   - Create an isolated working environment
   - Install all dependencies
   - Ask whether you want to download the AI models now (press Y and enter your Hugging Face token)
5. The first installation can take **10 to 40 minutes** depending on your internet speed and whether you download models

> If Windows blocks the PowerShell script, run this first in PowerShell: `Set-ExecutionPolicy -Scope Process Bypass`

---

## Step 4 — Open the app

- When the installation finishes, the app opens automatically
- To open it again in the future without reinstalling, **double-click** **`open_spanishfly.bat`**

---

## What SpanishFly includes today

- **Persona** — AI character editor: generate character images from a description, reference image, and style settings
- **Storyboard, Video, Voice** — Coming soon

---

## Important files at a glance

| File | Purpose |
|---|---|
| `setup_spanishfly.bat` | Installs everything (double-click) |
| `open_spanishfly.bat` | Opens the app without reinstalling |
| `Persona/setup_persona.bat` | Installs only the Persona module |

---

## What the installer checks

The installer verifies your system and shows a results table:

| Status | Meaning |
|---|---|
| OK | Requirement met |
| WARN | Warning: you can continue but performance may be lower |
| ERROR | Requirement not met: installation stops until you fix it |

---

## Persona editor guide

Once inside the app, in the Persona editor:

- **Character name** (required): identifies and saves the character
- **Reference image** (optional): photo or image the model will use as a style base
- **Prompt** (required): character description — English gives the best results
- **Image style**: visual preset applied automatically
- **Negative prompt**: what the model should avoid (pre-configured, editable)
- **Steps / CFG / Size / Seed**: advanced generation controls
- **ControlNet**: enables pose control with a reference image
- **NSFW mode**: activates the alternative model (requires prior download)

Generated images are saved in `Persona/outputs/personas/<name>/`.

---

## Security

- Do not upload `Persona/data/hf_credentials.json` to any public repository
- Model files and generated images are excluded from Git history by default
