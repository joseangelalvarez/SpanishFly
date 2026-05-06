from threading import Event
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from persona.core.generator import GenerationService
from persona.core.schemas import GenerationResult
from persona.infra.errors import GenerationCancelled


class GenerationWorker(QObject):
    progress = Signal(int, str)
    preview = Signal(str)
    completed = Signal(str, dict)
    failed = Signal(str)
    cancelled = Signal(str)

    def __init__(
        self,
        service: GenerationService,
        persona_name: str,
        prompt: str,
        cancel_event: Event,
        base_image_path: str | None = None,
        generation_options: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._persona_name = persona_name
        self._prompt = prompt
        self._cancel_event = cancel_event
        self._base_image_path = base_image_path
        self._generation_options = generation_options or {}

    @Slot()
    def run(self) -> None:
        try:
            result: GenerationResult = self._service.generate(
                persona_name=self._persona_name,
                prompt=self._prompt,
                cancel_event=self._cancel_event,
                progress_cb=self._on_progress,
                preview_cb=self._on_preview,
                base_image_path=self._base_image_path,
                **self._generation_options,
            )
            self.completed.emit(str(result.output_path), result.metadata)
        except GenerationCancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception as exc:
            text = str(exc)
            if "cancelada" in text.lower():
                self.cancelled.emit(text)
                return
            self.failed.emit(text)

    def _on_progress(self, value: int, message: str) -> None:
        self.progress.emit(value, message)

    def _on_preview(self, image_path: str) -> None:
        self.preview.emit(image_path)
