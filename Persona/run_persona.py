from pathlib import Path
import os
import subprocess
import sys


CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR / "src"
VENV_PY = CURRENT_DIR / "venv" / "Scripts" / "python.exe"
ROOT_DIR = CURRENT_DIR.parent


def _ensure_persona_venv() -> None:
    """Re-lanza con el venv de Persona si se invoca con otro interprete."""
    if not VENV_PY.exists():
        return

    current = Path(sys.executable).resolve()
    expected = VENV_PY.resolve()
    if current == expected:
        return

    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(VENV_PY.parent.parent)
    env["PYTHONPATH"] = str(SRC_DIR)
    env["SPANISHFLY_SKIP_BOOTSTRAP"] = "1"
    result = subprocess.run([str(expected), str(Path(__file__).resolve())], env=env, cwd=str(CURRENT_DIR))
    raise SystemExit(result.returncode)


def _bootstrap_persona_env() -> None:
    """Asegura dependencias coherentes del modulo antes de arrancar."""
    bootstrap_script = ROOT_DIR / "bootstrap_module_env.py"
    if not bootstrap_script.exists():
        return

    if os.environ.get("SPANISHFLY_SKIP_BOOTSTRAP") == "1":
        return

    env = os.environ.copy()
    env["SPANISHFLY_SKIP_BOOTSTRAP"] = "1"
    result = subprocess.run(
        [sys.executable, str(bootstrap_script), "persona"],
        cwd=str(ROOT_DIR),
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from persona.main import run


if __name__ == "__main__":
    _bootstrap_persona_env()
    _ensure_persona_venv()
    raise SystemExit(run())
