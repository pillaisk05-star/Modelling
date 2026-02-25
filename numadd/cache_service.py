class CacheService:
    def __init__(self):
        self._store = {}

    def get(self, a: float, b: float):
        key = self._build_key(a, b)
        return self._store.get(key)

    def set(self, a: float, b: float, value: float):
        key = self._build_key(a, b)
        self._store[key] = value

    def _build_key(self, a: float, b: float) -> str:
        return f"{a}+{b}"
