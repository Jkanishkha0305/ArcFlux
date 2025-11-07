from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "system_config.json"


def _resolve_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("env:"):
        env_key = value.split(":", 1)[1]
        return os.getenv(env_key)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


@lru_cache()
def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing system config at {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return _resolve_env(data)


def get_path(key: str) -> Path:
    config = load_config()
    data_paths = config.get("dataPaths", {})
    rel_path = data_paths.get(key)
    if not rel_path:
        raise KeyError(f"Config missing data path for '{key}'")
    return BASE_DIR / rel_path


__all__ = ["load_config", "get_path", "BASE_DIR"]
