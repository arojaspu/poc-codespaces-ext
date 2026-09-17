"""Lectura de las extensiones realmente instaladas en el Codespace."""

from __future__ import annotations

import re
import json
import shutil
import subprocess
from pathlib import Path

CANDIDATOS_DIR = [
    Path.home() / ".vscode-remote" / "extensions",
    Path.home() / ".vscode-server" / "extensions",
    Path.home() / ".vscode" / "extensions",
]

_PATRON_ID_VALIDO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*\.[A-Za-z0-9][A-Za-z0-9-]*$")

def _id_desde_nombre_carpeta(nombre: str) -> str:
    return _PATRON_ID_VALIDO.sub("", nombre)

def _via_cli() -> list[str] | None:
    """Fuente primaria: la CLI del editor."""
    binario = shutil.which("code") or shutil.which("code-insiders")
    if not binario:
        return None
    try:
        salida = subprocess.run(
            [binario, "--list-extensions"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if salida.returncode != 0:
        return None
    candidatas = (linea.strip() for linea in salida.stdout.splitlines())
    return sorted({c for c in candidatas if _PATRON_ID_VALIDO.fullmatch(c)})


def _via_disco() -> list[str]:
    """Fuente secundaria: el disco.

    Importante para la PoC: detecta extensiones copiadas a mano en el
    directorio de extensiones, que la CLI puede no reportar.
    """
    encontradas: set[str] = set()
    for base in CANDIDATOS_DIR:
        manifest = base / "extensions.json"
        if manifest.exists():
            try:
                for item in json.loads(manifest.read_text(encoding="utf-8")):
                    ident = item.get("identifier", {}).get("id")
                    if ident:
                        encontradas.add(ident)
            except (OSError, ValueError):
                pass
        if base.is_dir():
            for carpeta in base.iterdir():
                if carpeta.is_dir() and (carpeta / "package.json").exists():
                    nombre = carpeta.name.rsplit("-", 1)[0]
                    if "." in nombre:
                        encontradas.add(nombre)

                if carpeta.is_dir() and (carpeta / "package.json").exists():
                    nombre = _id_desde_nombre_carpeta(carpeta.name)  # <- antes: carpeta.name.rsplit("-", 1)[0]
                    if "." in nombre:
                        encontradas.add(nombre)
    return sorted(encontradas)


def instaladas() -> tuple[list[str], str]:
    """Devuelve (lista de extension ids, fuente usada)."""
    por_cli = _via_cli()
    en_disco = _via_disco()
    if por_cli is None:
        return en_disco, "disco"
    union = sorted(set(por_cli) | set(en_disco))
    fuente = "cli" if set(union) == set(por_cli) else "cli+disco"
    return union, fuente


def desinstalar(extension_id: str) -> tuple[bool, str]:
    binario = shutil.which("code") or shutil.which("code-insiders")
    if not binario:
        return False, "CLI 'code' no disponible"
    salida = subprocess.run(
        [binario, "--uninstall-extension", extension_id],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    ok = salida.returncode == 0
    return ok, (salida.stdout + salida.stderr).strip()[:400]
