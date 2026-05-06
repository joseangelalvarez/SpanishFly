# SpanishFly Suite — Italiano

SpanishFly e una suite modulare di contenuti IA locale per creator che vogliono risultati professionali senza complessita tecnica.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

---

## Cosa ti serve prima di iniziare

Prima di installare, assicurati di avere:

- **Windows 10 o Windows 11** (64 bit)
- **Almeno 16 GB di RAM** e **30 GB di spazio libero su disco**
- **GPU NVIDIA consigliata** con 8 GB di VRAM o piu (funziona anche senza GPU, ma molto piu lentamente)
- **Connessione internet** per l installazione e il download dei modelli
- Un **account gratuito su Hugging Face** per scaricare i modelli IA (vedi passo 2)

---

## Passo 1 — Scarica il progetto

1. Clicca il pulsante verde **Code** in cima a questa pagina di GitHub
2. Seleziona **Download ZIP**
3. Estrai la cartella ZIP in un posto sul tuo computer (es. Desktop o `C:\SpanishFly`)

> Puoi anche clonare con Git se sai come fare: `git clone https://github.com/joseangelalvarez/SpanishFly.git`

---

## Passo 2 — Crea il tuo account e token su Hugging Face

SpanishFly scarica i suoi modelli IA da Hugging Face. Hai bisogno di un account gratuito e di un token di accesso.

1. Crea un account su [https://huggingface.co/join](https://huggingface.co/join)
2. Verifica la tua email e accedi
3. Vai su [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Clicca su **New token**, seleziona il tipo **Read** e dagli un nome (es. `spanishfly`)
5. Copia il token — inizia con `hf_...` — ti servirà durante l installazione

> Il token viene salvato solo sul tuo computer, in `Persona/data/hf_credentials.json`. Non condividerlo mai.

---

## Passo 3 — Avvia l installatore

1. Apri la cartella dove hai estratto SpanishFly
2. **Fai doppio clic** sul file **`setup_spanishfly.bat`**
3. Se Windows chiede se ti fidi del file, clicca su **"Esegui comunque"**
4. L installatore si aprira in una finestra nera (console) e fara tutto automaticamente:
   - Controllare i requisiti di sistema e avvisarti se qualcosa e sotto il minimo
   - Installare Python 3.10 automaticamente (non devi installarlo tu)
   - Creare un ambiente di lavoro isolato
   - Installare tutte le dipendenze
   - Chiederti se vuoi scaricare ora i modelli IA (premi Y e inserisci il tuo token Hugging Face)
5. La prima installazione puo richiedere **tra 10 e 40 minuti** a seconda della velocita di connessione e se scarichi i modelli

> Se Windows blocca lo script PowerShell, esegui prima in PowerShell: `Set-ExecutionPolicy -Scope Process Bypass`

---

## Passo 4 — Apri l applicazione

- Al termine dell installazione, l applicazione si apre automaticamente
- Per riaprirla in futuro senza reinstallare, **fai doppio clic** su **`open_spanishfly.bat`**

---

## Cosa include SpanishFly oggi

- **Persona** — Editor di personaggi IA: genera immagini di personaggi da una descrizione, un immagine di riferimento e impostazioni di stile
- **Storyboard, Video, Voce** — In arrivo

---

## File importanti in sintesi

| File | Scopo |
|---|---|
| `setup_spanishfly.bat` | Installa tutto (doppio clic) |
| `open_spanishfly.bat` | Apre l app senza reinstallare |
| `Persona/setup_persona.bat` | Installa solo il modulo Persona |

---

## Cosa verifica l installatore

L installatore controlla il tuo sistema e mostra una tabella dei risultati:

| Stato | Significato |
|---|---|
| OK | Requisito soddisfatto |
| WARN | Avviso: puoi continuare ma le prestazioni potrebbero essere ridotte |
| ERROR | Requisito non soddisfatto: l installazione si ferma finche non lo correggi |

---

## Guida all editor Persona

Una volta nell applicazione, nell editor Persona:

- **Nome personaggio** (obbligatorio): identifica e salva il personaggio
- **Immagine di riferimento** (opzionale): foto o immagine che il modello usera come base di stile
- **Prompt** (obbligatorio): descrizione del personaggio — l inglese da i migliori risultati
- **Stile immagine**: preset visivo applicato automaticamente
- **Prompt negativo**: cosa il modello deve evitare (pre-configurato, modificabile)
- **Steps / CFG / Dimensione / Seed**: controlli avanzati di generazione
- **ControlNet**: attiva il controllo della posa con un immagine di riferimento
- **Modalita NSFW**: attiva il modello alternativo (richiede download preventivo)

Le immagini generate vengono salvate in `Persona/outputs/personas/<nome>/`.

---

## Sicurezza

- Non caricare `Persona/data/hf_credentials.json` su nessun repository pubblico
- I file dei modelli e le immagini generate sono esclusi dalla cronologia Git per impostazione predefinita
