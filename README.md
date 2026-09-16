# PoC — Restricción de extensiones en GitHub Codespaces

**Hipótesis (H1):** el ajuste `extensions.allowed`, declarado en
`customizations.vscode.settings` del `devcontainer.json`, se aplica dentro del
Codespace y **no puede ser sobrescrito** por los settings de usuario.

Si H1 es cierta, existe un control preventivo. Si es falsa, lo único disponible
es control detectivo/correctivo y la PoC debe reorientarse.

Alcance: 3 días, en 3 fases con entregable propio. Ver `docs/PLAN-3-DIAS.md`.

---

## Arquitectura en 30 segundos

| Capa | Artefacto | Tipo de control |
|---|---|---|
| Política | `policy/allowlist.yaml` | Fuente única de verdad |
| Preventivo | `.devcontainer/devcontainer.json` → `extensions.allowed` | Bloquea la instalación |
| Detectivo/correctivo | `tools/ext_guard/` | Detecta y revierte |
| Gobierno | `CODEOWNERS` + `.github/workflows/ci.yml` | Impide desincronizar la política |

`policy/allowlist.yaml` es lo único que se edita a mano. El bloque
`extensions.allowed` del devcontainer se genera con `python -m ext_guard render`,
y el CI falla si ambos divergen.

---

## Uso

```bash
python -m ext_guard check                    # instaladas vs allowlist
python -m ext_guard check --json --label CP-05
python -m ext_guard check --enforce          # además desinstala
python -m ext_guard render                   # regenera extensions.allowed
python -m ext_guard drift                    # devcontainer vs allowlist
python -m ext_guard report                   # resumen de evidencia
python -m ext_guard verify                   # integridad de la cadena
```

La evidencia se acumula en `docs/evidencias/eventos.jsonl`, con hash encadenado:
si alguien edita o borra una línea del historial, `verify` lo detecta.

---

## Qué NO hace esta PoC

El desarrollador tiene `sudo` dentro del Codespace. `ext_guard` puede ser
detenido (`pkill -f ext_guard`) y no pretende ser una barrera: su valor es dejar
rastro y acotar la ventana de exposición.

El único control verdaderamente duro es la política de dispositivo
(`AllowedExtensions` vía GPO/Intune) en equipos gestionados con VS Code Desktop,
y queda fuera del alcance de estos 3 días.

---

## Estructura

```
.devcontainer/    devcontainer.json + post-create.sh
.vscode/          recomendaciones y settings del workspace
policy/           allowlist.yaml  <- fuente de verdad
src/inventario/   app Python mínima (da trabajo real al entorno)
tests/            pruebas de la app y del guard
tools/ext_guard/  CLI de control
docs/             plan de 3 días, protocolo y evidencias
.github/          CI: lint + tests + control de drift
```
