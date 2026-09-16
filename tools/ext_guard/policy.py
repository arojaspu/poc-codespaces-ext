"""Carga y normalizacion de policy/allowlist.yaml."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__).resolve()).resolve()
    for parent in [here, *here.parents]:
        if (parent / "policy" / "allowlist.yaml").exists():
            return parent
    raise FileNotFoundError("no se encontro policy/allowlist.yaml subiendo desde " + str(here))


@dataclass
class Policy:
    version: int
    mode: str
    allowed_ids: set[str]
    allowed_publishers: set[str]
    test_targets: list[str]
    tolerated_prefixes: list[str]
    path: Path

    @classmethod
    def load(cls, path: Path | None = None) -> Policy:
        path = path or (repo_root() / "policy" / "allowlist.yaml")
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        ids: set[str] = set()
        publishers: set[str] = set()
        for entry in raw.get("allowed", []):
            if not isinstance(entry, dict):
                raise ValueError(f"entrada invalida en allowed: {entry!r}")
            if "id" in entry:
                ids.add(str(entry["id"]).lower())
            elif "publisher" in entry:
                publishers.add(str(entry["publisher"]).lower())
            else:
                raise ValueError(f"entrada sin 'id' ni 'publisher': {entry!r}")

        mode = str(raw.get("mode", "audit")).lower()
        if mode not in {"audit", "enforce"}:
            raise ValueError(f"mode invalido: {mode}")

        return cls(
            version=int(raw.get("version", 1)),
            mode=mode,
            allowed_ids=ids,
            allowed_publishers=publishers,
            test_targets=[str(t) for t in raw.get("test_targets", [])],
            tolerated_prefixes=[str(p).lower() for p in raw.get("tolerated_prefixes", [])],
            path=path,
        )

    def permite(self, extension_id: str) -> bool:
        ext = extension_id.lower()
        if ext in self.allowed_ids:
            return True
        publisher = ext.split(".", 1)[0]
        return publisher in self.allowed_publishers

    def tolerada(self, extension_id: str) -> bool:
        ext = extension_id.lower()
        return any(ext.startswith(p) for p in self.tolerated_prefixes)

    def as_vscode_allowed(self) -> dict[str, bool]:
        """Bloque 'extensions.allowed' equivalente, para el devcontainer.json."""
        bloque: dict[str, bool] = {ext: True for ext in sorted(self.allowed_ids)}
        for pub in sorted(self.allowed_publishers):
            bloque[pub] = True
        bloque["*"] = False
        return bloque

    def render(self) -> str:
        return json.dumps(self.as_vscode_allowed(), indent=2, ensure_ascii=False)
