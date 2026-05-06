import json
from dataclasses import dataclass, field
from pathlib import Path

from persona.infra.errors import ConfigError
from persona.infra.pathing import ensure_dir, resolve_path


@dataclass(slots=True)
class RuntimeConfig:
    device_preference: str
    dtype: str
    height: int
    width: int
    steps: int
    guidance_scale: float
    seed: int | None
    negative_prompt: str


@dataclass(slots=True)
class ModelConfig:
    sdxl_base_path: Path
    sdxl_nsfw_path: Path | None
    controlnet_paths: list[Path]
    ip_adapter_paths: dict[str, Path]
    sdxl_hf_repo: str = ""
    sdxl_nsfw_hf_repo: str = ""
    controlnet_hf_repos: list[str] = field(default_factory=list)
    ip_adapter_hf_repos: dict[str, str] = field(default_factory=dict)
    ip_adapter_subfolders: dict[str, str] = field(default_factory=dict)
    ip_adapter_weights: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class AppConfig:
    persona_root: Path
    data_personas_dir: Path
    outputs_personas_dir: Path
    runtime: RuntimeConfig
    models: ModelConfig


def load_app_config(persona_root: Path, config_path: Path) -> AppConfig:
    if not config_path.exists():
        raise ConfigError(f"No existe configuracion: {config_path}")

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    runtime_raw = raw.get("runtime", {})
    model_raw = raw.get("models", {})
    outputs_raw = raw.get("outputs", {})

    runtime = RuntimeConfig(
        device_preference=runtime_raw.get("device_preference", "cuda"),
        dtype=runtime_raw.get("dtype", "float16"),
        height=int(runtime_raw.get("height", 1216)),
        width=int(runtime_raw.get("width", 832)),
        steps=int(runtime_raw.get("steps", 35)),
        guidance_scale=float(runtime_raw.get("guidance_scale", 4.0)),
        seed=runtime_raw.get("seed", 2554065581),
        negative_prompt=runtime_raw.get("negative_prompt", ""),
    )

    models = ModelConfig(
        sdxl_base_path=resolve_path(persona_root, model_raw.get("sdxl_base_path", "models/sdxl/base")),
        sdxl_nsfw_path=(
            resolve_path(persona_root, model_raw.get("sdxl_nsfw_path"))
            if model_raw.get("sdxl_nsfw_path")
            else None
        ),
        sdxl_hf_repo=model_raw.get("sdxl_hf_repo", ""),
        sdxl_nsfw_hf_repo=model_raw.get("sdxl_nsfw_hf_repo", ""),
        controlnet_paths=[resolve_path(persona_root, p) for p in model_raw.get("controlnet_paths", [])],
        controlnet_hf_repos=model_raw.get("controlnet_hf_repos", []),
        ip_adapter_paths={
            key: resolve_path(persona_root, path)
            for key, path in model_raw.get("ip_adapter_paths", {}).items()
        },
        ip_adapter_hf_repos=model_raw.get("ip_adapter_hf_repos", {}),
        ip_adapter_subfolders=model_raw.get("ip_adapter_subfolders", {}),
        ip_adapter_weights=model_raw.get("ip_adapter_weights", {}),
    )

    outputs_dir = resolve_path(persona_root, outputs_raw.get("base_dir", "outputs/personas"))
    data_personas_dir = ensure_dir(persona_root / "data" / "personas")

    return AppConfig(
        persona_root=persona_root,
        data_personas_dir=data_personas_dir,
        outputs_personas_dir=ensure_dir(outputs_dir),
        runtime=runtime,
        models=models,
    )
