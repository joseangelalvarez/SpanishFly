# SpanishFly Suite — Deutsch

SpanishFly ist eine modulare lokale KI-Inhaltssuite fur Creator, die professionelle Ergebnisse ohne technische Komplexitat wollen.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

---

## Was du vor dem Start benotigst

Stelle vor der Installation sicher, dass du Folgendes hast:

- **Windows 10 oder Windows 11** (64 Bit)
- **Mindestens 16 GB RAM** und **30 GB freier Speicherplatz**
- **NVIDIA GPU empfohlen** mit 8 GB VRAM oder mehr (funktioniert auch ohne GPU, aber viel langsamer)
- **Internetverbindung** fur die Installation und den Modell-Download
- Ein **kostenloses Hugging Face Konto**, um die KI-Modelle herunterzuladen (siehe Schritt 2)

---

## Schritt 1 — Projekt herunterladen

1. Klicke auf den grunen **Code**-Button oben auf dieser GitHub-Seite
2. Wahle **Download ZIP**
3. Entpacke den ZIP-Ordner irgendwo auf deinem Computer (z.B. Desktop oder `C:\SpanishFly`)

> Du kannst auch mit Git klonen, wenn du weist wie: `git clone https://github.com/joseangelalvarez/SpanishFly.git`

---

## Schritt 2 — Hugging Face Konto und Token erstellen

SpanishFly ladt seine KI-Modelle von Hugging Face herunter. Du benotigst ein kostenloses Konto und einen Zugriffstoken.

1. Erstelle ein Konto auf [https://huggingface.co/join](https://huggingface.co/join)
2. Verifiziere deine E-Mail und melde dich an
3. Gehe zu [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Klicke auf **New token**, wahle Typ **Read** und gib ihm einen Namen (z.B. `spanishfly`)
5. Kopiere den Token — er beginnt mit `hf_...` — du wirst ihn wahrend der Installation brauchen

> Der Token wird nur auf deinem Computer gespeichert, in `Persona/data/hf_credentials.json`. Teile ihn niemals.

---

## Schritt 3 — Installer ausfuhren

1. Offne den Ordner, in den du SpanishFly entpackt hast
2. **Doppelklicke** auf die Datei **`setup_spanishfly.bat`**
3. Wenn Windows fragt, ob du der Datei vertraust, klicke auf **"Trotzdem ausfuhren"**
4. Der Installer offnet sich in einem schwarzen Fenster (Konsole) und erledigt alles automatisch:
   - Systemvoraussetzungen prufen und dich warnen, wenn etwas unter dem Minimum liegt
   - Python 3.10 automatisch installieren (du musst es nicht selbst installieren)
   - Eine isolierte Arbeitsumgebung erstellen
   - Alle Abhangigkeiten installieren
   - Fragen, ob du die KI-Modelle jetzt herunterladen mochtest (drucke J oder Y und gib deinen Hugging Face Token ein)
5. Die erste Installation kann **10 bis 40 Minuten** dauern, je nach Internetgeschwindigkeit und ob du Modelle herunterlädst

> Wenn Windows das PowerShell-Skript blockiert, fuhre zuerst in PowerShell aus: `Set-ExecutionPolicy -Scope Process Bypass`

---

## Schritt 4 — App offnen

- Wenn die Installation abgeschlossen ist, offnet sich die App automatisch
- Um sie spater ohne Neuinstallation zu offnen, **doppelklicke** auf **`open_spanishfly.bat`**

---

## Was SpanishFly heute enthalt

- **Persona** — KI-Charakter-Editor: Generiere Charakterbilder aus einer Beschreibung, einem Referenzbild und Stileinstellungen
- **Storyboard, Video, Stimme** — In Entwicklung

---

## Wichtige Dateien auf einen Blick

| Datei | Zweck |
|---|---|
| `setup_spanishfly.bat` | Installiert alles (Doppelklick) |
| `open_spanishfly.bat` | Offnet die App ohne Neuinstallation |
| `Persona/setup_persona.bat` | Installiert nur das Persona-Modul |

---

## Was der Installer pruft

Der Installer pruft dein System und zeigt eine Ergebnistabelle:

| Status | Bedeutung |
|---|---|
| OK | Anforderung erfullt |
| WARN | Warnung: du kannst fortfahren, aber die Leistung kann geringer sein |
| ERROR | Anforderung nicht erfullt: Installation stoppt bis zur Behebung |

---

## Persona Editor Anleitung

Sobald du in der App bist, im Persona-Editor:

- **Charaktername** (Pflicht): identifiziert und speichert den Charakter
- **Referenzbild** (optional): Foto oder Bild, das das Modell als Stilbasis verwendet
- **Prompt** (Pflicht): Charakterbeschreibung — Englisch liefert die besten Ergebnisse
- **Bildstil**: visuelles Preset, das automatisch angewendet wird
- **Negativprompt**: was das Modell vermeiden soll (vorkonfiguriert, editierbar)
- **Steps / CFG / Grosse / Seed**: erweiterte Generierungssteuerung
- **ControlNet**: aktiviert Posenkontrolle mit einem Referenzbild
- **NSFW-Modus**: aktiviert das alternative Modell (erfordert vorherigen Download)

Generierte Bilder werden in `Persona/outputs/personas/<name>/` gespeichert.

---

## Sicherheit

- Veroffentliche `Persona/data/hf_credentials.json` nicht in einem offentlichen Repository
- Modelldateien und generierte Bilder sind standardmasig aus der Git-Historie ausgeschlossen
