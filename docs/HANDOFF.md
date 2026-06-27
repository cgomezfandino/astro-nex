# Astro-Nex — Handoff (punto de control)

> **Lee esto al iniciar cada sesión.** Captura el estado y el siguiente paso.
> Metodología detallada en `docs/WORKING-STYLE.md`.
>
> Última actualización: 2026-06-28 (Phase 2E empaquetado .app completo, 350 tests).

## Estado actual (verificado con evidencia)

| Hito | Estado | Ref |
|---|---|---|
| Phase 1 (slice Py3/GTK3) | ✅ DONE | v0.1.0 |
| Phase 2A — Cimientos de datos | ✅ DONE, mergeado | milestone #4 closed |
| Phase 2B — Motor de cálculo | ✅ DONE, mergeado, 252 tests | milestone #5 closed |
| Phase 2C-core — Render core | ✅ DONE, mergeado, 333 tests | milestone #6 (parcial) |
| Phase 2D-mvp — GUI usable | ✅ DONE, mergeado, 350 tests | milestone #7 (mvp) |
| **Phase 2E — .app empaquetado** | ✅ **DONE, mergeado, app arranca + relocatable** | milestone #2 (parcial) |
| Phase 2D-advanced (diálogos) | ⏳ Pendiente | #23-#31 |
| Phase 2E — Empaquetado .app | ⏳ Pendiente | milestone #2 |
| **Phase 2C-core — Render core** | ✅ **DONE, mergeado, QA verde, 333 tests** | milestone #6 (2C-core parcial) |
| Phase 2C-advanced (biograph/planetogram) | ⏳ Pendiente | #22 |
| Phase 2C-synastry (paarwabe) | ⏳ Pendiente | #21 |
| Phase 2D–2E | ⏳ Pendientes | milestones #7, #2 |

- **`main`**: sincronizada con `origin/main`, working tree limpio, sin ramas colgadas.
- **Tests**: **252 pasando** (baseline 2A era 125 → +127 en 2B).
- **Issues 2B**: #16, #17, #18, #5 trabajados, testeados y listos para cerrar.

## Qué es el proyecto

Modernización de **Astro-Nex 1.2.3** (método API/Huber, GPLv3, autor José Antonio
Rodríguez 1960–2022, mantenido en su honor). Objetivo: app macOS `.app` ejecutable
con doble clic + soporte multiplataforma (Win/Linux/macOS). Repo del port:
`/Users/cgomezfandino/repos/astro-nex` · GitHub: `cgomezfandino/astro-nex`.

**Decisión clave**: port completo a Py3/GTK3 primero → empaquetado `.app` al final.
El slice actual es ~7% del código; el motor de cálculo está completo, falta
render (2C) y GUI (2D).

## ━━ Phase 2B cerrada — qué se hizo ━━

Todos los issues verificados **contra el original corriendo en Docker** (golden),
con review subagent aprobado por cada uno.

| Issue | Qué | Detalle |
|---|---|---|
| **#16** directions | solar_rev + sec_prog | `core/directions.py`. solar_rev con bisección (~40 evals vs 6 bucles legacy); **bug C1 cazado por review** (wraparound 0/360 en equinoccio) arreglado + bloqueado con golden. +22 tests. |
| **NeXDate** | setdt/set_now/set_delta/dateforstore/getnewdt | Cierra el ciclo con `Current`. Política `fold=0` (fidelidad a `is_dst=True`). +10 tests. |
| **#18** chart types | Tier A/B/C/D | 9 transformaciones puras (exact 1e-9), local_houses, pers_force (Huber), contrato Transits. +66 tests. |
| **#5** tz_sup | **Obsoleto bajo zoneinfo** | Cerrado con tests: zoneinfo maneja LMT nativamente, más preciso que el legacy (15/16 fechas de transición del legacy estaban mal). +6 tests. |
| **#17** Age Point | puntero + timetable | `core/age_point.py`: puntero Lebensuhr (radix+nodal, exact 1e-9) + timetable calc_agep radix (955 eventos verificados elemento-por-elemento; sort-stability Py2→Py3 resuelto). +33 tests. |

### Hallazgos clave de 2B
- **Paridad verificada** contra el legacy real corriendo en Docker, sin modificar.
- **Golden harness reproducible** (`tools/original-docker/gen_golden.sh`) — regenera
  cualquier golden con un comando.
- **Sort-stability**: el timetable reproduce el orden exacto del legacy Py2 via
  `cmp_to_key` + append order idéntico.
- **Mejoras sobre el legacy** (sin romper cálculos): solar_rev converge mejor,
  tz_sup más preciso, bug del equinoccio arreglado.

### Variantes diferidas (no bloquean)
- `calc_nodal_agep`, `calc_house_agep`, `calc_house_nodal_agep` (variantes del
  timetable; radix es el default de la GUI).
- `calc_agep(local=True)` (relocated-houses).
- `calc_plan_with_retrogression`, `chiron_calc`, `vulcan_calc`, dynamics.

## ━━ Phase 2C-core cerrada — qué se hizo ━━

El render core está portado con el **patrón del port** (funciones puras en
`render/`, NO la jerarquía mixin/chartob del legacy). Verificado con smoke +
comparación visual humana (no golden — es trabajo visual).

| Tarea | Qué | Detalle |
|---|---|---|
| **Dynamics** (calc) | signdyn, housedyn, dyncalc_list, dynstar_*, cuad_plan, rays_calc, calc_cross_points | Golden-exact (5 datasets). Desbloquea datasheets/diagrams. |
| **Aspect geometry** | 5 formas Huber (Fusus, Conjunctio, Unilateral, Goodwill, AgePoint) | 0 acoplamiento boss. `render/aspects.py`. |
| **Wheel multi-tipo** | draw_wheel (radix/soul/house/dharma/nodal/ur_nodal/local) | `render/wheel.py` extendido; draw_radix = alias. |
| **Datasheets** | tabla planetas + matriz aspectos 12×12 + dynamics + rays | `render/datasheets.py`. |
| **Diagrams** | composite dynamics (signs/houses/energy/differences/bars) | `render/diagrams.py`. |

### Lo que queda de 2C (no bloquea)

| Issue | Qué | Por qué diferido |
|---|---|---|
| #22 | biograph + planetogram + profchart + progsheet | Análisis avanzado; alta deuda calc (calc_pe_houses, plagram_*analysis). |
| #21 | paarwabe (3.296 LOC) | Sinastria/parejas — subsistema distinto; depende de jerarquía chartob dual. |
| parcial | dyn_cuad/dyn_cuad2 (quadrant interactivo), datasheets house/nodal variants | Click-chart / variants menores. |

## ━━ Phase 2D-mvp cerrada — qué se hizo ━━

La **GUI usable** está completa, construida SOBRE el core/render ya portados
(no portando el legacy GTK2). El flujo principal funciona end-to-end:

> entrar datos de nacimiento → seleccionar tipo de carta (7 kinds) → ver
> (rueda/hoja de datos/diagrama) → exportar PNG/PDF que coincide con la pantalla

| Tarea | Qué |
|---|---|
| ChartView multi-modo | view_mode (wheel/datasheet/diagram) + kind (7 tipos), dispatch a render/ |
| ChartEntry validación | try/except + MessageDialog; campos first/last name; text fields |
| MainWindow selectores | combos view-mode + chart-type; "Local" recomputa houses |
| Exporters kind/view_mode | export_png/pdf threadean los params (archivo = pantalla) |
| Wiring Current | MainWindow replica el chart en state.master (desbloquea save/pool futuro) |

### Lo que queda de 2D (no bloquea)
- Diálogos avanzados: browser de DB, config, calendar popup, place search,
  couples/cycles (paarwabe/biograph). Son features; el mvp da la app usable.
- boss.Manager god-object, slot/master-click swap, ~40 keyboard accelerators.

## ━━ Phase 2E cerrada — qué se hizo ━━

La app es ahora un **`.Astro-Nex.app` de doble clic** (hybrid bundle). El build
vive en `tools/build_macos_app.py` + `tools/macos/` (aditivo, no toca src/).

> `python3 tools/build_macos_app.py` → genera `dist/Astro-Nex.app` (11MB),
> la firma ad-hoc, lanza y verifica que arranca, y comprueba relocatable.

**Approach híbrido** (decidido tras topar con codesign + framework-Python en el
approach embebido): el `.app` embebe astronex + launcher + icono + Info.plist y
referencia el Python + GTK de Homebrew en runtime via DYLD/GI env. Robusto y
compacto. El **bundle embebido completo** (sin dependencia de Homebrew) queda
como objetivo de seguimiento (requiere resolver Python standalone + dylib
rewriting + firma bottom-up de sub-bundles).

Launcher: PYTHONPATH al paquete embebido, GI/GDK/XDG a Homebrew, lockfile
instancia única, auto-diagnóstico en fallo (`~/Library/Logs/Astro-Nex/app.log`
+ diálogo osascript).

Verificado: build idempotente, app arranca y se mantiene viva, relocatable
(abre desde /tmp), no-regresión (350 tests).

## ━━ SIGUIENTE PASO ━━

El producto entregable está completo (app de doble clic funcional). Opciones:
- **2E-followup**: bundle embebido completo (sin Homebrew) + `.dmg` instalable
  + firma Developer ID/notarización (~99 USD/año Apple).
- **2D-advanced**: diálogos del legacy (browser DB, config, place search,
  couples/cycles = paarwabe/biograph).
- **2C-advanced**: biograph/planetogram (#22), paarwabe sinastria (#21).
- **Phase 3**: integración con Astro Soul Center (envolver core/ en API).

## Dependencias a recordar
- `core/` está **completo y testeado** (config, state, chart, directions, age_point,
  nexdate, ephemeris, utils, timezones, constants). Puro, sin GUI.
- 2C consume `core/` directamente (chart planets/houses, age_point timetable,
  directions solar_rev/sec_prog).
- `Current` (state.py) sigue con métodos pendientes que mutan estado (setchart,
  setprogchart, setloc) — esos son de la capa GUI (2D), no del cálculo.

## Documentación importante

- `docs/WORKING-STYLE.md` — **cómo trabajamos** (brainstorm→TDD→QA→ciclar). Leer.
- `docs/ROADMAP.md` — fases y sub-milestones.
- `CHANGELOG.md` — historial de cambios (entrada Phase 2B añadida).
- `docs/superpowers/specs/2026-06-27-directions-port-design.md` — spec de directions (#16).
- `docs/superpowers/plans/2026-06-27-directions-port.md` — plan de directions.
- `docs/superpowers/specs/2026-06-27-macos-app-bundling-design.md` — spec del `.app`.
- `tools/original-docker/` — harness para comparar contra el original (golden).

## Snapshot técnico de 2B (para contexto)

Golden files (reproducibles via `gen_golden.sh`): `ephemeris.json`, `directions.json`,
`chart_types.json`, `age_point.json`, `age_timetable.json` — 5 datasets cada uno
(incl. caso equinoccio que bloquea el bug C1).

Sanity verificados: PNGs renderizados correctamente (natal, solar return), paridad
numérica port-vs-legacy a 1e-6°, smoke test e2e (calc→chart→png).
