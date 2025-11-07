from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable, Optional


class JSONDataStore:
    """Thread-safe helper for working with JSON files."""

    _locks = {}

    def __init__(self, path: Path, default_factory: Optional[Callable[[], Any]] = None) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.default_factory = default_factory or (lambda: [])
        if path not in self._locks:
            self._locks[path] = threading.RLock()
        self.lock: threading.RLock = self._locks[path]
        if not self.path.exists():
            self.save(self.default_factory())

    def load(self) -> Any:
        with self.lock:
            with self.path.open("r", encoding="utf-8") as fh:
                return json.load(fh)

    def save(self, data: Any) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with self.lock:
            with tmp_path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            tmp_path.replace(self.path)

    def update(self, mutator: Callable[[Any], Any]) -> Any:
        with self.lock:
            data = self.load()
            mutated = mutator(data)
            self.save(mutated)
            return mutated

    def append(self, record: Any) -> Any:
        def _mutator(data: Any) -> Any:
            if not isinstance(data, list):
                raise TypeError(f"append only supported for list-based stores, found {type(data)}")
            data.append(record)
            return data

        return self.update(_mutator)


__all__ = ["JSONDataStore"]
