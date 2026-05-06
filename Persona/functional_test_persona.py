#!/usr/bin/env python3
"""
Prueba funcional del modulo Persona (sin UI interactiva):
1) Valida configuración y modelos locales
2) Ejecuta una generación real reducida
3) Valida cancelación segura durante inferencia
4) Verifica persistencia JSON con metadatos
"""
from __future__ import annotations

import sys
from pathlib import Path
from threading import Event


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from persona.config.settings import load_app_config
from persona.core.generator import GenerationService
from persona.core.model_registry import ModelRegistry
from persona.core.persona_store import PersonaStore
from persona.core.schemas import PersonaRecord, now_iso
from persona.infra.errors import GenerationCancelled


def run_generation_smoke_test(cfg) -> tuple[str, dict]:
    service = GenerationService(cfg)
    cancel_event = Event()

    progress_events: list[tuple[int, str]] = []

    def progress_cb(value: int, message: str) -> None:
        progress_events.append((value, message))
        print(f"[GEN] {value:3d}% | {message}")

    result = service.generate(
        persona_name="functional_test",
        prompt="portrait, cinematic lighting, detailed face, vertical composition",
        cancel_event=cancel_event,
        progress_cb=progress_cb,
        base_image_path=None,
    )

    if not result.output_path.exists():
        raise RuntimeError(f"La imagen no se generó: {result.output_path}")

    required_meta = ["device", "width", "height", "steps", "generated_at"]
    missing_meta = [k for k in required_meta if k not in result.metadata]
    if missing_meta:
        raise RuntimeError(f"Metadata incompleta en resultado: faltan {missing_meta}")

    print(f"[OK] Imagen generada en: {result.output_path}")
    return str(result.output_path), result.metadata


def run_cancellation_test(cfg) -> None:
    service = GenerationService(cfg)
    cancel_event = Event()

    def progress_cb(value: int, message: str) -> None:
        print(f"[CAN] {value:3d}% | {message}")
        if value >= 60:
            cancel_event.set()

    try:
        service.generate(
            persona_name="functional_cancel",
            prompt="test cancellation flow",
            cancel_event=cancel_event,
            progress_cb=progress_cb,
            base_image_path=None,
        )
    except GenerationCancelled:
        print("[OK] Cancelación capturada correctamente.")
        return

    raise RuntimeError("La generación no se canceló como se esperaba.")


def run_persistence_test(cfg, image_path: str, metadata: dict) -> None:
    store = PersonaStore(cfg.data_personas_dir)
    name = "functional_test"

    record = PersonaRecord(
        name=name,
        base_image_path="",
        created_at=now_iso(),
        notes="Prueba funcional automatizada",
        base_prompt="portrait, cinematic lighting, detailed face, vertical composition",
        last_generated_image=image_path,
        last_generation_metadata=metadata,
    )
    path = store.save(record)
    loaded = store.load(name)

    if loaded is None:
        raise RuntimeError("No se pudo leer el JSON persistido del personaje.")
    if loaded.last_generated_image != image_path:
        raise RuntimeError("last_generated_image no coincide en JSON persistido.")
    if not loaded.last_generation_metadata or "generated_at" not in loaded.last_generation_metadata:
        raise RuntimeError("last_generation_metadata no se guardó correctamente.")

    print(f"[OK] Persistencia validada en: {path}")


def main() -> int:
    print("=" * 80)
    print("PRUEBA FUNCIONAL - SpanishFly Persona")
    print("=" * 80)

    cfg = load_app_config(persona_root=ROOT, config_path=ROOT / "config_persona.json")
    registry = ModelRegistry(cfg.models)
    registry.validate_local_paths()
    print("[OK] Modelos locales obligatorios encontrados.")

    # Reducir costo para test funcional rápido.
    cfg.runtime.steps = 2
    cfg.runtime.width = 512
    cfg.runtime.height = 896

    image_path, metadata = run_generation_smoke_test(cfg)

    # Subir pasos para tener margen de cancelación durante callbacks.
    cfg.runtime.steps = 20
    run_cancellation_test(cfg)

    run_persistence_test(cfg, image_path=image_path, metadata=metadata)

    print("\nRESULTADO: PRUEBA FUNCIONAL EXITOSA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
