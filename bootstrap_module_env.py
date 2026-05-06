from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class BootstrapError(RuntimeError):
    pass


@dataclass(slots=True)
class ModuleBootstrapConfig:
    key: str
    module_dir: Path
    requirements_file: Path
    install_torch: bool


@dataclass(slots=True)
class ModuleEnvironmentInfo:
    python_executable: str
    venv_dir: str
    torch_profile: str


MODULES: dict[str, ModuleBootstrapConfig] = {
    "persona": ModuleBootstrapConfig(
        key="persona",
        module_dir=ROOT / "Persona",
        requirements_file=ROOT / "Persona" / "requirements.txt",
        install_torch=True,
    ),
}


def _venv_python(venv_dir: Path) -> Path:
    if platform.system().lower().startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=True,
    )


def _detect_cuda_profile() -> tuple[str, str]:
    """
    Returns (profile, index_url).
    profile: cpu | cu118 | cu124 | cu128
    """
    nvidia_smi = "nvidia-smi"
    try:
        result = _run([nvidia_smi, "--query-gpu=compute_cap", "--format=csv,noheader"])
    except Exception:
        return "cpu", "https://download.pytorch.org/whl/cpu"

    line = result.stdout.strip().splitlines()[0].strip() if result.stdout.strip() else ""
    if not line or "." not in line:
        return "cpu", "https://download.pytorch.org/whl/cpu"

    major_str, minor_str = line.split(".", 1)
    try:
        cc = int(major_str) * 10 + int(minor_str)
    except ValueError:
        return "cpu", "https://download.pytorch.org/whl/cpu"

    if cc >= 89:
        return "cu128", "https://download.pytorch.org/whl/cu128"
    if cc >= 80:
        return "cu124", "https://download.pytorch.org/whl/cu124"
    if cc >= 70:
        return "cu118", "https://download.pytorch.org/whl/cu118"
    return "cpu", "https://download.pytorch.org/whl/cpu"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _state_file(module_dir: Path) -> Path:
    return module_dir / "venv" / ".module_env_state.json"


def _load_state(module_dir: Path) -> dict:
    sf = _state_file(module_dir)
    if not sf.exists():
        return {}
    try:
        return json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(module_dir: Path, state: dict) -> None:
    sf = _state_file(module_dir)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_module_environment(module_key: str, force: bool = False) -> ModuleEnvironmentInfo:
    cfg = MODULES.get(module_key.lower())
    if cfg is None:
        raise BootstrapError(f"Modulo desconocido: {module_key}")

    module_dir = cfg.module_dir
    requirements = cfg.requirements_file
    if not module_dir.exists():
        raise BootstrapError(f"No existe directorio del modulo: {module_dir}")
    if not requirements.exists():
        raise BootstrapError(f"No existe requirements del modulo: {requirements}")

    venv_dir = module_dir / "venv"
    py = _venv_python(venv_dir)

    if not py.exists():
        try:
            _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=module_dir)
        except subprocess.CalledProcessError as exc:
            raise BootstrapError(f"No se pudo crear venv para {cfg.key}:\n{exc.stderr or exc.stdout}") from exc

    torch_profile, torch_index = _detect_cuda_profile()
    req_hash = _sha256(requirements)
    desired_state = {
        "module": cfg.key,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "requirements_sha256": req_hash,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "torch_profile": torch_profile if cfg.install_torch else "n/a",
    }

    current_state = _load_state(module_dir)
    if (not force) and current_state == desired_state:
        return ModuleEnvironmentInfo(
            python_executable=str(py),
            venv_dir=str(venv_dir),
            torch_profile=desired_state["torch_profile"],
        )

    try:
        _run([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=module_dir)

        if cfg.install_torch:
            if torch_profile == "cpu":
                torch_pkgs = [
                    "torch==2.11.0",
                    "torchvision==0.26.0",
                    "torchaudio==2.11.0",
                ]
            else:
                torch_pkgs = [
                    f"torch==2.11.0+{torch_profile}",
                    f"torchvision==0.26.0+{torch_profile}",
                    f"torchaudio==2.11.0+{torch_profile}",
                ]

            _run(
                [str(py), "-m", "pip", "install", "--upgrade", "--index-url", torch_index, *torch_pkgs],
                cwd=module_dir,
            )

        _run([str(py), "-m", "pip", "install", "-r", str(requirements)], cwd=module_dir)
    except subprocess.CalledProcessError as exc:
        output = exc.stderr or exc.stdout or str(exc)
        raise BootstrapError(f"No se pudo preparar entorno de {cfg.key}:\n{output}") from exc

    _save_state(module_dir, desired_state)
    return ModuleEnvironmentInfo(
        python_executable=str(py),
        venv_dir=str(venv_dir),
        torch_profile=desired_state["torch_profile"],
    )


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python bootstrap_module_env.py <modulo> [--force]")
        print(f"Modulos: {', '.join(sorted(MODULES.keys()))}")
        return 2

    module_key = sys.argv[1]
    force = "--force" in sys.argv[2:]

    try:
        info = ensure_module_environment(module_key=module_key, force=force)
    except BootstrapError as exc:
        print(str(exc))
        return 1

    print(json.dumps({
        "module": module_key,
        "python_executable": info.python_executable,
        "venv_dir": info.venv_dir,
        "torch_profile": info.torch_profile,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
