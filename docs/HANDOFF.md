# Astro-Nex — Handoff / Punto de control

> Documento vivo que captura el estado del proyecto para poder retomarlo sin pérdida.
> Actualizado: 2026-06-27 (tras cerrar Phase 2A).

## Qué es este proyecto

Modernización de **Astro-Nex 1.2.3** — software astrológico del método **API/Huber**
(Bruno & Louise Huber), GPLv3, creado por **José Antonio Rodríguez (1960–2022)**,
mantenido en su honor.

- **Repo original** (Python 2 + PyGTK 2 + GTK 2, muerto en macOS moderno):
  `/Users/cgomezfandino/repos/Astro-Nex-1.2.3`
- **Repo del port** (Python 3.12+ + GTK 3):
  `/Users/cgomezfandino/repos/astro-nex`
- **GitHub**: https://github.com/cgomezfandino/astro-nex (cuenta `cgomezfandino`, `gh` autenticado)

## Objetivo

App macOS **ejecutable con doble clic** (`.app` autocontenido, GTK embebido, icono
en Dock) **+** mantener el soporte multiplataforma existente (Windows, Linux,
macOS-por-terminal). Distribuible a la comunidad.

## Decisión arquitectica clave

**Port completo a Py3/GTK3 primero → empaquetado `.app` al final.**
El "port" de la Fase 1 era solo un slice mínimo (~4% del código: 1084 de 28639 LOC).
Para que macOS tenga "las mismas capacidades" del screenshot de referencia, primero
hay que portar toda la funcionalidad restante (eso sirve igual para Win/Linux/macOS,
pues el código `src/` es multiplataforma). El empaquetado son ~2 días al final.

## Estado actual (punto de control)

| Hito | Estado | SHA / ref |
|---|---|---|
| Phase 1 (slice Py3/GTK3) | ✅ DONE | v0.1.0 |
| **Phase 2A (cimientos de datos)** | ✅ **DONE, mergeado a main, pusheado** | `9b72fee` |
| Phase 2B (motor de cálculo) | ⏳ Pendiente | milestone GitHub #5 |
| Phase 2C (motor de dibujo) | ⏳ Pendiente | milestone GitHub #6 |
| Phase 2D (GUI completa) | ⏳ Pendiente | milestone GitHub #7 |
| Phase 2E (empaquetado macOS) | ⏳ Pendiente | milestone GitHub #2 |

**Tests**: 125 pasando (en venv limpio). Bug real cazado por TDD (store_chart).

## Cómo retomar el trabajo

1. `cd /Users/cgomezfandino/repos/astro-nex && git pull`
2. Verificar baseline: `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/python -m pytest -q` → 125 passed.
3. El siguiente hito es **Phase 2B** (milestone #5). Ver `gh issue list --milestone "2B..."`.
4. Crear worktree aislado: `git worktree add .worktrees/2B-calc -b milestone-2B-calc`.
5. Trabajar con TDD por cada issue (#16 directions, #17 Age Point, #18 tipos de carta, #5 tz_sup).
6. Al cerrar 2B: smoke test de integración → cerrar issues → merge a main → push → cerrar milestone.

## Documentación importante

- **ROADMAP**: `docs/ROADMAP.md` (estado de fases y sub-milestones).
- **CHANGELOG**: `CHANGELOG.md`.
- **Spec empaquetado macOS**: `docs/superpowers/specs/2026-06-27-macos-app-bundling-design.md`.
- **Plan Fase 1**: `docs/superpowers/plans/2026-06-26-astro-nex-py3-gtk3-vertical-slice.md`.
- **Docker original (referencia)**: `tools/original-docker/`.

## Reglas de oro del proyecto

1. **TDD estricto**: RED → GREEN → REFACTOR. Sin código de producción sin test que falle primero.
2. **Verificación con evidencia**: nunca afirmar "hecho/pasa" sin correr el comando y leer la salida.
3. **Fidelidad al original**: comparar contra Docker/golden data. El cálculo debe coincidir (≤1e-4°).
4. **Aditivo/no intrusivo**: el empaquetado macOS no toca `src/` (sigue multiplataforma).
5. **Worktree aislado por milestone**: protege `main`, ramas con nombre `milestone-2X-...`.
6. **Puntos de control**: commitear y pusheado frecuentemente; este documento captura el estado.
