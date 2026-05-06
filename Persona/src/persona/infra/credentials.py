import json
from pathlib import Path


_CREDENTIALS_FILE = Path(__file__).resolve().parents[3] / "data" / "hf_credentials.json"


def load_credentials() -> tuple[str, str]:
    if _CREDENTIALS_FILE.exists():
        try:
            data = json.loads(_CREDENTIALS_FILE.read_text(encoding="utf-8"))
            return data.get("username", ""), data.get("token", "")
        except Exception:
            pass
    return "", ""


def save_credentials(username: str, token: str) -> None:
    _CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CREDENTIALS_FILE.write_text(
        json.dumps({"username": username, "token": token}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
