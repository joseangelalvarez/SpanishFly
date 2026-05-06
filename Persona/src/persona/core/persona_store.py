import json
from dataclasses import asdict
from pathlib import Path

from persona.core.schemas import PersonaRecord, persona_json_name
from persona.infra.pathing import ensure_dir


class PersonaStore:
    def __init__(self, personas_dir: Path) -> None:
        self._personas_dir = ensure_dir(personas_dir)

    def save(self, record: PersonaRecord) -> Path:
        file_path = self._personas_dir / persona_json_name(record.name)
        payload = asdict(record)
        file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return file_path

    def load(self, name: str) -> PersonaRecord | None:
        file_path = self._personas_dir / persona_json_name(name)
        if not file_path.exists():
            return None
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        return PersonaRecord(**raw)
