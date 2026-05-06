# SpanishFly Suite — Francais

SpanishFly est une suite modulaire de creation IA locale pour les createurs qui veulent des resultats professionnels sans complexite technique.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

---

## Ce dont vous avez besoin avant de commencer

Avant d installer, assurez-vous d avoir :

- **Windows 10 ou Windows 11** (64 bits)
- **Au moins 16 Go de RAM** et **30 Go d espace disque libre**
- **GPU NVIDIA recommande** avec 8 Go de VRAM ou plus (fonctionne aussi sans GPU, mais beaucoup plus lentement)
- **Connexion internet** pour l installation et le telechargement des modeles
- Un **compte Hugging Face gratuit** pour telecharger les modeles IA (voir etape 2)

---

## Etape 1 — Telecharger le projet

1. Cliquez sur le bouton vert **Code** en haut de cette page GitHub
2. Selectionnez **Download ZIP**
3. Extrayez le dossier ZIP quelque part sur votre ordinateur (par exemple, Bureau ou `C:\SpanishFly`)

> Vous pouvez aussi cloner avec Git si vous savez comment : `git clone https://github.com/joseangelalvarez/SpanishFly.git`

---

## Etape 2 — Creer votre compte et token Hugging Face

SpanishFly telecharge ses modeles IA depuis Hugging Face. Vous avez besoin d un compte gratuit et d un token d acces.

1. Creez un compte sur [https://huggingface.co/join](https://huggingface.co/join)
2. Verifiez votre email et connectez-vous
3. Allez sur [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Cliquez sur **New token**, selectionnez le type **Read** et donnez-lui un nom (ex. : `spanishfly`)
5. Copiez le token — il commence par `hf_...` — vous en aurez besoin pendant l installation

> Le token est stocke uniquement sur votre ordinateur, dans `Persona/data/hf_credentials.json`. Ne le partagez jamais.

---

## Etape 3 — Lancer l installateur

1. Ouvrez le dossier ou vous avez extrait SpanishFly
2. **Double-cliquez** sur le fichier **`setup_spanishfly.bat`**
3. Si Windows vous demande si vous faites confiance au fichier, cliquez sur **"Executer quand meme"**
4. L installateur s ouvrira dans une fenetre noire (console) et fera tout automatiquement :
   - Verifier vos prerequis systeme et vous avertir si quelque chose est en dessous du minimum
   - Installer Python 3.10 automatiquement (vous n avez pas besoin de l installer vous-meme)
   - Creer un environnement de travail isole
   - Installer toutes les dependances
   - Vous demander si vous voulez telecharger les modeles IA maintenant (tapez Y et entrez votre token Hugging Face)
5. La premiere installation peut prendre **entre 10 et 40 minutes** selon votre connexion et si vous telechargez les modeles

> Si Windows bloque le script PowerShell, executez d abord dans PowerShell : `Set-ExecutionPolicy -Scope Process Bypass`

---

## Etape 4 — Ouvrir l application

- A la fin de l installation, l application s ouvre automatiquement
- Pour la rouvrir plus tard sans reinstaller, **double-cliquez** sur **`open_spanishfly.bat`**

---

## Ce qu inclut SpanishFly aujourd hui

- **Persona** — Editeur de personnages IA : generez des images de personnages a partir d une description, d une image de reference et de parametres de style
- **Storyboard, Video, Voix** — Bientot disponibles

---

## Fichiers importants en un coup d oeil

| Fichier | Utilite |
|---|---|
| `setup_spanishfly.bat` | Installe tout (double-clic) |
| `open_spanishfly.bat` | Ouvre l app sans reinstaller |
| `Persona/setup_persona.bat` | Installe uniquement le module Persona |

---

## Ce que l installateur verifie

L installateur controle votre systeme et affiche un tableau de resultats :

| Statut | Signification |
|---|---|
| OK | Prerequis satisfait |
| WARN | Avertissement : vous pouvez continuer mais les performances peuvent etre reduites |
| ERROR | Prerequis non satisfait : l installation s arrete jusqu a correction |

---

## Guide de l editeur Persona

Une fois dans l application, dans l editeur Persona :

- **Nom du personnage** (obligatoire) : identifie et sauvegarde le personnage
- **Image de reference** (optionnel) : photo ou image que le modele utilisera comme base de style
- **Prompt** (obligatoire) : description du personnage — l anglais donne les meilleurs resultats
- **Style d image** : preset visuel applique automatiquement
- **Prompt negatif** : ce que le modele doit eviter (pre-configure, modifiable)
- **Steps / CFG / Taille / Seed** : controles avances de generation
- **ControlNet** : active le controle de pose avec une image de reference
- **Mode NSFW** : active le modele alternatif (necessite un telechargement prealable)

Les images generees sont sauvegardees dans `Persona/outputs/personas/<nom>/`.

---

## Securite

- Ne publiez pas `Persona/data/hf_credentials.json` dans un depot public
- Les fichiers de modeles et les images generees sont exclus de l historique Git par defaut
