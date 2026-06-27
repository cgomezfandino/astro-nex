# Astro-Nex — Handoff (punto de control)

> **Lee esto al iniciar cada sesión.** Captura el estado y el siguiente paso.
> Metodología detallada en `docs/WORKING-STYLE.md`.
>
> Última actualización: 2026-06-27 (Phase 2C-core render completa, 333 tests).

## Estado actual (verificado con evidencia)

| Hito | Estado | Ref |
|---|---|---|
| Phase 1 (slice Py3/GTK3) | ✅ DONE | v0.1.0 |
| Phase 2A — Cimientos de datos | ✅ DONE, mergeado | milestone #4 closed |
| Phase 2B — Motor de cálculo | ✅ DONE, mergeado, 252 tests | milestone #5 closed |
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

## ━━ SIGUIENTE PASO: Phase 2D (GUI) ━━

El cálculo Y el render core están completos. La siguiente fase es **2D · GUI**
(milestone #7): portar la ventana GTK3, paneles y diálogos que consumen el
`core/` + `render/` ya portados. Issues #23-#31.

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
