import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class _Entry:
    value: object
    expires_at: float


@dataclass
class TTLCache:
    ttl_seconds: float = 600.0
    max_size: int = 256
    _data: dict[str, _Entry] = field(default_factory=dict, init=False)

    def get(self, key: str) -> object | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            del self._data[key]
            return None
        return entry.value

    def set(self, key: str, value: object) -> None:
        if len(self._data) >= self.max_size:
            oldest = min(self._data, key=lambda k: self._data[k].expires_at)
            del self._data[oldest]
        self._data[key] = _Entry(value=value, expires_at=time.monotonic() + self.ttl_seconds)

    def clear(self) -> None:
        self._data.clear()
