# Plan de ejecución — PoC en 3 días

## Principio de recorte

De los 5 grupos y ~35 casos del diseño original se conserva **solo la ruta
crítica**: lo que responde si H1 es cierta y, si lo es, hasta dónde aguanta.
Todo lo demás se declara fuera de alcance de forma explícita, no se omite en
silencio.

### Fuera de alcance (documentado, no probado)
JetBrains Gateway · bloqueo de egress de red · pinning por versión y
pre-release · prebuilds · extension packs y dependencias · features de
devcontainer que instalan extensiones · dotfiles personales · política de
dispositivo (GPO/Intune) · marketplace privado de GitHub Enterprise.

Cada uno se menciona en el informe final como brecha conocida con su
mitigación propuesta, para que la decisión se tome con el mapa completo.

---

## Fase 1 — Go / No-Go (Día 1)

Objetivo: **decidir si la PoC sigue siendo una PoC de control preventivo.**

| ID | Caso | Cómo | Resultado esperado |
|---|---|---|---|
| CP-01 | Línea base | Crear Codespace desde `main`, ejecutar `python -m ext_guard check --json --label CP-01` | Exactamente las 4 extensiones del allowlist, más las inyectadas por la plataforma |
| CP-02 | **H1: la política se aplica** | Abrir Settings, buscar `extensions.allowed` | Aparece marcada como gestionada (icono de maletín / *Managed by organization*) con el valor del devcontainer |
| CP-03 | **Override del usuario** | En el `settings.json` de usuario poner `"extensions.allowed": {"*": true}`, recargar ventana, intentar instalar `esbenp.prettier-vscode` | El valor del devcontainer prevalece y la instalación sigue bloqueada |
| CP-04 | Entorno funcional | `pytest -q` y `ruff check .` | Todo pasa: la restricción no rompe el trabajo diario |

### Puerta de decisión (fin del Día 1)

- **CP-02 y CP-03 pasan** → H1 confirmada. Continuar con la Fase 2 tal cual.
- **CP-02 pasa, CP-03 falla** → el control es cosmético: cualquiera lo desactiva.
  La Fase 2 se reduce a documentar el fallo y la Fase 3 pasa a ser el plan
  principal (`ext_guard` en modo `enforce` + gobierno).
- **CP-02 falla** → `extensions.allowed` no se honra desde el devcontainer.
  Saltar directamente a Fase 3 y escalar la ruta de política de dispositivo.

**Entregable Fase 1:** una página con el veredicto de H1, capturas de CP-02 y
CP-03, y la rama de plan elegida.

---

## Fase 2 — Cobertura de vectores (Día 2)

Objetivo: **medir qué vectores de instalación cubre realmente el control.**
Se prueban los ordinarios, que son los que explican la gran mayoría de los casos
reales, más los dos que se sabe que son problemáticos.

| ID | Vector | Comando / acción | Esperado |
|---|---|---|---|
| CP-05 | UI del Marketplace | Buscar `esbenp.prettier-vscode` → *Install* | Botón deshabilitado o error de política |
| CP-06 | CLI | `code --install-extension esbenp.prettier-vscode` | Rechazado |
| CP-07 | VSIX | Subir el `.vsix` → *Install from VSIX…* y `code --install-extension ./x.vsix` | Rechazado en ambas vías |
| CP-08 | Copia manual | Descomprimir el VSIX en `~/.vscode-remote/extensions/` y recargar ventana | **Bypass probable.** Medir si `ext_guard check` lo detecta |
| CP-09 | Settings Sync | Iniciar sesión con una cuenta que sincroniza extensiones no aprobadas | Documentar si llegan y si son revertidas |
| CP-10 | Cliente | Repetir CP-05 y CP-06 desde VS Code Desktop y desde el navegador | Comparar: la diferencia define la política de acceso |

Cada caso se registra con `python -m ext_guard check --json --label CP-0X`
antes y después, de modo que la evidencia quede encadenada.

**Entregable Fase 2:** matriz *vector × resultado × captura*, con los bypass
marcados en rojo.

---

## Fase 3 — Red de seguridad e informe (Día 3)

Objetivo: **cubrir lo que la capa preventiva deja fuera y cerrar con una
recomendación.**

| ID | Caso | Cómo | Esperado |
|---|---|---|---|
| CP-11 | Guard en modo audit | Provocar CP-08, ejecutar `check --json` | La violación queda registrada con timestamp y hash |
| CP-12 | Guard en modo enforce | `mode: enforce` en el allowlist, `check --enforce` | La extensión no aprobada se desinstala |
| CP-13 | Rebuild | *Rebuild Container* tras una violación | El entorno vuelve al estado aprobado |
| CP-14 | Gobierno | PR que modifica `devcontainer.json` sin tocar `allowlist.yaml` | El job de drift falla y bloquea el merge |

**Entregable Fase 3 (informe final):**
1. Veredicto de H1 en una frase.
2. Matriz vector × capa que lo cubre × resultado observado.
3. Brechas conocidas (lo que quedó fuera de alcance) con mitigación propuesta.
4. Recomendación explícita: ¿viable para producción tal cual, viable con
   control de dispositivo, o no viable?

---

## Criterio de éxito de la PoC

La PoC es **exitosa** si CP-02 y CP-03 pasan y si CP-05 a CP-07 quedan
bloqueados. Eso significa que existe un control preventivo real contra los
vectores ordinarios.

Cualquier vector no bloqueado no invalida la PoC **siempre que quede
documentado con su compensación**. Lo que sí la invalidaría es entregar un
control que solo parece restringir.
