"""Evidencia en JSONL con hash encadenado.

Cada registro incluye el hash del anterior. Si alguien edita o borra una
linea del historial, la cadena se rompe y 'verify' lo detecta.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

GENESIS = "0" * 64


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ultimo_hash(archivo: Path) -> str:
    if not archivo.exists():
        return GENESIS
    ultima = None
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            ultima = linea
    if ultima is None:
        return GENESIS
    return json.loads(ultima)["hash"]


def registrar(archivo: Path, evento: dict) -> dict:
    archivo.parent.mkdir(parents=True, exist_ok=True)
    registro = {
        "ts": datetime.now(UTC).isoformat(),
        "usuario": os.environ.get("GITHUB_USER") or os.environ.get("USER", "desconocido"),
        "codespace": os.environ.get("CODESPACE_NAME", "local"),
        "prev": _ultimo_hash(archivo),
        **evento,
    }
    registro["hash"] = _hash(json.dumps(registro, sort_keys=True, ensure_ascii=False))
    with archivo.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def verificar(archivo: Path) -> tuple[bool, str]:
    if not archivo.exists():
        return True, "sin evidencia registrada"
    anterior = GENESIS
    for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), start=1):
        if not linea.strip():
            continue
        registro = json.loads(linea)
        esperado = registro.pop("hash")
        if registro["prev"] != anterior:
            return False, f"cadena rota en la linea {n}: 'prev' no coincide"
        if _hash(json.dumps(registro, sort_keys=True, ensure_ascii=False)) != esperado:
            return False, f"cadena rota en la linea {n}: contenido alterado"
        anterior = esperado
    return True, "cadena integra"
