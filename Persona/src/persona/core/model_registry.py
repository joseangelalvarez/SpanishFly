from pathlib import Path

from persona.config.settings import ModelConfig
from persona.core.download_task import DownloadTask
from persona.infra.errors import ModelLoadError


FACE_IP_ADAPTER_BIN = "ip-adapter-plus-face_sdxl_vit-h.bin"
FACE_IP_ADAPTER_SAFETENSORS = "ip-adapter-plus-face_sdxl_vit-h.safetensors"
SINGLE_FILE_MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".pt", ".pth"}


class ModelRegistry:
    def __init__(self, model_config: ModelConfig) -> None:
        self._cfg = model_config

    def validate_local_paths(self, nsfw_enabled: bool = False) -> None:
        """Valida que los artefactos obligatorios existan localmente."""
        selected_path = self._get_selected_base_model_path(nsfw_enabled=nsfw_enabled)
        if selected_path is None:
            raise ModelLoadError(
                "NSFW activado, pero no hay ruta de modelo NSFW configurada.\n"
                "Accion: agrega models.sdxl_nsfw_path en config_persona.json."
            )

        missing_required = self.get_missing_required_paths(nsfw_enabled=nsfw_enabled)
        if missing_required:
            lines = [
                "Faltan modelos locales obligatorios para iniciar la generación:",
                *[f"- {path}" for path in missing_required],
                "",
                "Accion: verifica config_persona.json y copia los modelos en esas rutas.",
            ]
            raise ModelLoadError("\n".join(lines))

    def get_missing_required_paths(self, nsfw_enabled: bool = False) -> list[Path]:
        missing: list[Path] = []
        base_model_path = self._get_selected_base_model_path(nsfw_enabled=nsfw_enabled)
        if base_model_path and not self._is_valid_model_location(base_model_path):
            missing.append(base_model_path)
        return missing

    def _is_valid_model_location(self, model_path: Path) -> bool:
        if not model_path.exists():
            return False

        if model_path.is_file():
            return model_path.suffix.lower() in SINGLE_FILE_MODEL_EXTENSIONS

        if model_path.is_dir():
            if (model_path / "model_index.json").exists():
                return True
            for candidate in model_path.iterdir():
                if candidate.is_file() and candidate.suffix.lower() in SINGLE_FILE_MODEL_EXTENSIONS:
                    return True
            return False

        return False

    def get_missing_optional_paths(self) -> list[Path]:
        missing: list[Path] = []
        for path in self._cfg.controlnet_paths:
            if not path.exists():
                missing.append(path)
        for path in self._cfg.ip_adapter_paths.values():
            if not path.exists():
                missing.append(path)

        face_root = self._cfg.ip_adapter_paths.get("face")
        if face_root and face_root.exists():
            face_subfolder = self._cfg.ip_adapter_subfolders.get("face", "sdxl_models")
            face_dir = face_root / face_subfolder if face_subfolder else face_root
            if not face_dir.exists():
                missing.append(face_dir)
            else:
                face_bin = face_dir / FACE_IP_ADAPTER_BIN
                face_safe = face_dir / FACE_IP_ADAPTER_SAFETENSORS
                if not face_bin.exists():
                    missing.append(face_bin)
                if not face_safe.exists():
                    missing.append(face_safe)

        return missing

    def get_missing_download_tasks(self, nsfw_enabled: bool = False) -> list[DownloadTask]:
        tasks: list[DownloadTask] = []

        base_model_path = self._get_selected_base_model_path(nsfw_enabled=nsfw_enabled)
        base_model_repo = self._get_selected_base_model_repo(nsfw_enabled=nsfw_enabled)
        if base_model_path and (not self._is_valid_model_location(base_model_path)) and base_model_repo:
            tasks.append(
                DownloadTask(
                    label="SDXL NSFW" if nsfw_enabled else "SDXL Base",
                    hf_repo_id=base_model_repo,
                    local_path=base_model_path,
                )
            )

        for i, path in enumerate(self._cfg.controlnet_paths):
            if path.exists():
                continue
            if i < len(self._cfg.controlnet_hf_repos) and self._cfg.controlnet_hf_repos[i]:
                tasks.append(
                    DownloadTask(
                        label=f"ControlNet {i + 1}",
                        hf_repo_id=self._cfg.controlnet_hf_repos[i],
                        local_path=path,
                    )
                )

        for key, path in self._cfg.ip_adapter_paths.items():
            if path.exists():
                continue
            repo_id = self._cfg.ip_adapter_hf_repos.get(key, "")
            if repo_id:
                tasks.append(
                    DownloadTask(
                        label=f"IP-Adapter ({key})",
                        hf_repo_id=repo_id,
                        local_path=path,
                    )
                )

        return tasks

    def _get_selected_base_model_path(self, nsfw_enabled: bool) -> Path | None:
        if nsfw_enabled:
            return self._cfg.sdxl_nsfw_path
        return self._cfg.sdxl_base_path

    def _get_selected_base_model_repo(self, nsfw_enabled: bool) -> str:
        if nsfw_enabled:
            return self._cfg.sdxl_nsfw_hf_repo
        return self._cfg.sdxl_hf_repo
