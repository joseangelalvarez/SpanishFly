from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DownloadTask:
    label: str
    hf_repo_id: str
    local_path: Path
