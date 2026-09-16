"""CLI de ext_guard.

  python -m ext_guard check     compara instaladas vs allowlist (exit 1 si hay violaciones)
  python -m ext_guard check --enforce   ademas desinstala las no aprobadas
  python -m ext_guard render    imprime el bloque extensions.allowed del devcontainer
  python -m ext_guard drift     valida que devcontainer.json == allowlist.yaml
  python -m ext_guard report    resumen legible de la evidencia acumulada
  python -m ext_guard verify    verifica la integridad de la cadena de evidencia
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import evidence
from .inspector import desinstalar, instaladas
from .policy import Policy, repo_root

EVIDENCIA = "docs/evidencias/eventos.jsonl"


def _archivo_evidencia() -> Path:
    return repo_root() / EVIDENCIA


def _sin_comentarios(texto: str) -> str:
    """El devcontainer.json admite comentarios; json.loads no."""
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    texto = re.sub(r"^\s*//.*$", "", texto, flags=re.M)
    return re.sub(r",(\s*[}\]])", r"\1", texto)


def cmd_check(args: argparse.Namespace) -> int:
    policy = Policy.load()
    extensiones, fuente = instaladas()
    enforce = args.enforce or policy.mode == "enforce"

    violaciones, toleradas, aprobadas = [], [], []
    for ext in extensiones:
        if policy.permite(ext):
            aprobadas.append(ext)
        elif policy.tolerada(ext):
            toleradas.append(ext)
        else:
            violaciones.append(ext)

    acciones = []
    if enforce:
        for ext in violaciones:
            ok, detalle = desinstalar(ext)
            acciones.append({"extension": ext, "desinstalada": ok, "detalle": detalle})

    print(f"fuente de inventario : {fuente}")
    print(f"modo                 : {'enforce' if enforce else 'audit'}")
    print(f"aprobadas ({len(aprobadas)})        : {', '.join(aprobadas) or '-'}")
    print(f"toleradas ({len(toleradas)})        : {', '.join(toleradas) or '-'}")
    print(f"VIOLACIONES ({len(violaciones)})      : {', '.join(violaciones) or '-'}")
    for accion in acciones:
        estado = "desinstalada" if accion["desinstalada"] else "FALLO al desinstalar"
        print(f"  -> {accion['extension']}: {estado}")

    if args.json:
        registro = evidence.registrar(
            _archivo_evidencia(),
            {
                "evento": "check",
                "label": args.label,
                "modo": "enforce" if enforce else "audit",
                "fuente": fuente,
                "aprobadas": aprobadas,
                "toleradas": toleradas,
                "violaciones": violaciones,
                "acciones": acciones,
            },
        )
        print(f"\nevidencia: {_archivo_evidencia()} (hash {registro['hash'][:12]})")

    return 1 if violaciones else 0


def cmd_render(_: argparse.Namespace) -> int:
    print(Policy.load().render())
    return 0


def cmd_drift(_: argparse.Namespace) -> int:
    policy = Policy.load()
    devcontainer = repo_root() / ".devcontainer" / "devcontainer.json"
    datos = json.loads(_sin_comentarios(devcontainer.read_text(encoding="utf-8")))
    actual = datos["customizations"]["vscode"]["settings"].get("extensions.allowed", {})
    esperado = policy.as_vscode_allowed()

    if actual == esperado:
        print("OK: devcontainer.json coincide con policy/allowlist.yaml")
        return 0

    print("DRIFT detectado entre devcontainer.json y policy/allowlist.yaml\n")
    print("--- en devcontainer.json ---")
    print(json.dumps(actual, indent=2, sort_keys=True))
    print("\n--- esperado desde allowlist.yaml ---")
    print(json.dumps(esperado, indent=2, sort_keys=True))
    print("\nCorrige con: python -m ext_guard render")
    return 1


def cmd_report(_: argparse.Namespace) -> int:
    archivo = _archivo_evidencia()
    if not archivo.exists():
        print("sin evidencia registrada todavia")
        return 0
    total = violaciones = 0
    vistas: dict[str, int] = {}
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        registro = json.loads(linea)
        total += 1
        for ext in registro.get("violaciones", []):
            violaciones += 1
            vistas[ext] = vistas.get(ext, 0) + 1
        etiqueta = registro.get("label") or registro.get("evento")
        marca = "!" if registro.get("violaciones") else " "
        print(f"{marca} {registro['ts']}  {etiqueta:<24} violaciones={len(registro.get('violaciones', []))}")
    print(f"\ncorridas: {total} | violaciones acumuladas: {violaciones}")
    for ext, veces in sorted(vistas.items(), key=lambda kv: -kv[1]):
        print(f"  {ext}: {veces}")
    ok, detalle = evidence.verificar(archivo)
    print(f"integridad: {'OK' if ok else 'ALTERADA'} ({detalle})")
    return 0


def cmd_verify(_: argparse.Namespace) -> int:
    ok, detalle = evidence.verificar(_archivo_evidencia())
    print(f"{'OK' if ok else 'ALTERADA'}: {detalle}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ext_guard", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="comparar instaladas vs allowlist")
    p_check.add_argument("--enforce", action="store_true", help="desinstalar las no aprobadas")
    p_check.add_argument("--json", action="store_true", help="registrar evidencia JSONL")
    p_check.add_argument("--label", default="manual", help="etiqueta del caso de prueba")
    p_check.set_defaults(func=cmd_check)

    sub.add_parser("render", help="imprimir el bloque extensions.allowed").set_defaults(func=cmd_render)
    sub.add_parser("drift", help="validar devcontainer vs allowlist").set_defaults(func=cmd_drift)
    sub.add_parser("report", help="resumen de la evidencia").set_defaults(func=cmd_report)
    sub.add_parser("verify", help="verificar integridad de la evidencia").set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
