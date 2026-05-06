from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from persona.core.download_task import DownloadTask


class DownloadWorker(QObject):
    progress = Signal(int, str)
    task_done = Signal(str)
    all_done = Signal()
    failed = Signal(str)

    def __init__(self, tasks: list[DownloadTask], token: str, cancel_event: Event) -> None:
        super().__init__()
        self._tasks = tasks
        self._token = token
        self._cancel_event = cancel_event

    @Slot()
    def run(self) -> None:
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            self.failed.emit("huggingface_hub no esta instalado en el entorno.")
            return

        total = len(self._tasks)

        for i, task in enumerate(self._tasks):
            if self._cancel_event.is_set():
                self.failed.emit("Descarga cancelada por el usuario.")
                return

            pct = int(i / total * 100)
            self.progress.emit(pct, f"Descargando {task.label}  ({task.hf_repo_id})...")

            try:
                task.local_path.mkdir(parents=True, exist_ok=True)
                snapshot_download(
                    repo_id=task.hf_repo_id,
                    local_dir=str(task.local_path),
                    token=self._token,
                    ignore_patterns=[
                        # Formatos de otros frameworks (no necesarios para diffusers)
                        "*.onnx", "*.onnx_data",
                        "openvino_*", "onnx/*", "onnx_fp16/*",
                        "*.msgpack", "*.h5",
                        "flax_model*", "tf_model*", "rust_model*", "*.pb",
                        # Variante VAE opcional de SDXL (no se usa en el pipeline base)
                        "sd_xl_base_1.0_0.9vae.safetensors",
                        # Archivos de ejemplo e imagenes de documentacion
                        "*.png", "*.jpg", "*.jpeg",
                    ],
                )
                pct_done = int((i + 1) / total * 100)
                self.progress.emit(pct_done, f"Completado: {task.label}")
                self.task_done.emit(task.label)
            except Exception as exc:
                self.failed.emit(f"Error descargando {task.label}:\n{exc}")
                return

        self.progress.emit(100, "Todos los modelos descargados.")
        self.all_done.emit()
