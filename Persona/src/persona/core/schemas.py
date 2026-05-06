from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PersonaRecord:
    name: str
    base_image_path: str
    created_at: str
    notes: str
    base_prompt: str
    last_generated_image: str | None = None
    last_generation_metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class GenerationResult:
    output_path: Path
    metadata: dict[str, Any]


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def sanitize_name(name: str) -> str:
    safe = "".join(ch for ch in name.strip() if ch.isalnum() or ch in ("-", "_", " "))
    return safe.replace(" ", "_").lower() or "persona"


def output_file_name(persona_name: str) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{sanitize_name(persona_name)}_{stamp}.png"


def persona_json_name(persona_name: str) -> str:
    return f"{sanitize_name(persona_name)}.json"
